#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from dataclasses import dataclass, field
from json import JSONDecodeError
from time import perf_counter
from typing import Any, Optional

import mwparserfromhell as mwparser
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError


BLACKLIST = [ 'Q4115189', 'Q13406268', 'Q15397819', 'Q16943273', 'Q17339402']
WD = 'http://www.wikidata.org/entity/'
WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT = 'DeltaBot Complex Constraints'

REPORT_LIMIT = 5000
MAX_Q_TEMPLATE = 4000
TIMEOUT_LIMIT = 60


@dataclass
class ComplexConstraint:
    template:mwparser.wikicode.Wikicode

    error_msg:list[str] = field(default_factory=list)
    results:list[dict[str, Any]] = field(default_factory=list)
    query_timeout:bool = False

    label:str = field(init=False)
    sparql:str = field(init=False)
    description:Optional[str] = None

    query_http_status:int = field(init=False)
    query_time:float = field(init=False)
    result_cnt:int = field(init=False)
    vars:list[str] = field(init=False)

    def __post_init__(self) -> None:
        self._parse_template_params()


    def _parse_template_params(self) -> None:
        template_dict = self.dictify_constraint_template(self.template)
        self._parse_param_label(template_dict.get('label'))
        self._parse_param_sparql(template_dict.get('sparql'))
        self._parse_param_description(template_dict.get('description'))
        self._parse_unknown_params(list(template_dict.keys()))


    def _parse_param_label(self, label:Optional[str]) -> None:
        if label is None or label=='':
            err = 'Required parameter "label" is missing'
            self.error_msg.append(err)
            raise ValueError(err)
        self.label = label


    def _parse_param_sparql(self, sparql:Optional[str]) -> None:
        if sparql is None or sparql=='':
            err = 'Required parameter "sparql" is missing'
            self.error_msg.append(err)
            raise ValueError(err)
        self.sparql = sparql.replace('{{!!}}', '||').replace('{{!}}', '|')


    def _parse_param_description(self, description:Optional[str]) -> None:
        if description is None or description=='':
            return  # param is optional
        self.description = description


    def _parse_unknown_params(self, params:list[str]) -> None:
        for key in params:
            if key in ['label', 'description', 'sparql']:
                continue
            self.error_msg.append(f'Constraint definition has {len(params)-3} invalid template parameters')
            break


    def evaluate(self) -> None:
        self._query_and_parse()


    @staticmethod
    def _sortkey(val:dict[str, dict[str, str]]) -> int:
        try:
            sortkey = int(val.get('item', {}).get('value', '')[len(WD)+1:])
        except ValueError:  # senses, forms, other oddities, etc.
            sortkey = 0
        
        return sortkey


    def _query_and_parse(self) -> None:
        payload = {
            'query' : self.sparql,
            'format' : 'json'
        }

        time_start = perf_counter()
        try:
            response = requests.post(
                WDQS_ENDPOINT,
                data=payload,
                headers={ 'User-Agent' : WDQS_USER_AGENT }
            )
        except (ChunkedEncodingError, ConnectionError) as exception:
            self.error_msg.append(f'Experienced {exception.__class__.__name__} during querying')
            self.result_cnt = 0
            self.query_time = perf_counter() - time_start
            self.query_http_status = 0
            if self.query_time > TIMEOUT_LIMIT:
                self.query_timeout = True
            return
        self.query_time = perf_counter() - time_start

        self.query_http_status = response.status_code

        try:
            data = response.json()
        except JSONDecodeError:
            self.result_cnt = 0

            if response.status_code==400 and self.query_time < 1:
                self.error_msg.append(f'Cannot parse WDQS response as JSON object (likely reason: malformed query)')
                return

            if self.query_time > TIMEOUT_LIMIT:
                self.query_timeout = True
                self.error_msg.append(f'Cannot parse WDQS response as JSON object (likely reason: query timeout)')
                return

            self.error_msg.append(f'Cannot parse WDQS response as JSON object (reason unknown)')
            return

        if 'item' not in data.get('head', {}).get('vars', []):
            self.error_msg.append(f'No "?item" parameter defined in query')
            self.result_cnt = 0
            return

        self.vars = [ var for var in data.get('head', {}).get('vars', []) if var != 'item' ]
        self.results = sorted(
            [ row for row in data.get('results', {}).get('bindings', []) if row.get('item', {}).get('value', '')[len(WD):] not in BLACKLIST ],
            key=self._sortkey,
        )
        self.result_cnt = len(self.results)


    def _compile_section_header_template(self) -> str:
        if len(self.error_msg)==0:
            error_str = ''
        else:
            error_str = f'<code>{"</code><br><code>".join(self.error_msg)}</code>'

        text = f"""{{{{Complex constraint section header
|label={self.label}
|description={self.description or ''}
|sparql={self.sparql.replace('|', '{{!}}')}
|violations={self.result_cnt}
|query_http_status={self.query_http_status}
|query_time={self.query_time:.2f}
|query_timeout={self.query_timeout}
|errors={error_str}
}}}}

"""

        return text


    def write_section_for_constraint_violation_report(self, q_template_cnt:int) -> tuple[str, int]:
        text = f'\n== {self.label} ==\n'
        text += self._compile_section_header_template()

        if self.query_timeout is True:
            return text, q_template_cnt

        if self.result_cnt == 0:
            return text, q_template_cnt

        for row in self.results[:REPORT_LIMIT]:
            qid = row.get('item', {}).get('value', '')
            qid_formatted, q_template_cnt = self.format_q_p(qid, q_template_cnt)

            text += f'* {qid_formatted}'
            values = []
            for var in self.vars:
                value = row.get(var, {}).get('value', '')
                value_formatted, q_template_cnt = self.format_q_p(value, q_template_cnt)
                values.append(value_formatted)
            if len(values) > 0:
                text += f': {", ".join(values)}'
            text += '\n'

        if self.result_cnt > REPORT_LIMIT:
            text += f'\nThis complex constraint violation list is limited to {REPORT_LIMIT} cases; {self.result_cnt - REPORT_LIMIT} cases have been skipped.\n'

        return text, q_template_cnt


    @staticmethod
    def dictify_constraint_template(template:mwparser.wikicode.Wikicode) -> dict[str, str]:
        data:dict[str, str] = {}

        for param in template.params:
            data[str(param.name).strip().lower()] = str(param.value).strip()

        return data

    @staticmethod
    def format_q_p(val:str, q_template_cnt:int) -> tuple[str, int]:
        if not val.startswith(WD):  # all non-entity values
            val = val.replace('T00:00:00Z', '')
            return val, q_template_cnt

        val = val.replace(WD, '')

        if q_template_cnt < MAX_Q_TEMPLATE:
            if val.startswith('Q'):
                return f'{{{{Q|{val}}}}}', q_template_cnt+1

            if val.startswith('P'):
                return f'{{{{P|{val}}}}}', q_template_cnt+1

            if val.startswith('L'):
                return f'{{{{Lexeme|{val}}}}}', q_template_cnt+4 # +4 because this template seems particularly expensive

        if val.startswith('Q'):
            return f'[[{val}]]', q_template_cnt

        if val.startswith('P'):
            return f'[[Property:{val}]]', q_template_cnt

        if val.startswith('L'):
            return f'[[Lexeme:{val}]]'.replace('-', '#'), q_template_cnt

        return val, q_template_cnt