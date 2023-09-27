#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from time import strftime

from .PageWithComplexConstraintDefinition import PageWithComplexConstraintDefinition
from .bot import edit_page


def write_overview(reports:list[PageWithComplexConstraintDefinition]) -> None:
    table_row = """{{{{TR complex constraint
|p={entity}
|label={label}
|description={description}
|violations={violations}
|query_http_status={query_http_status}
|query_time={query_time:.2f}
|query_timeout={query_timeout}
|errors={errors}
}}}}\n"""
    text = f'{{{{/header|{strftime("%Y-%m-%d")}}}}}\n\n'

    for report in reports:
        for constraint in report.constraints:
            if len(constraint.error_msg)==0:
                error_str = ''
            else:
                error_str = f'<code>{"</code><br><code>".join(constraint.error_msg)}</code>'

            text += table_row.format(
                entity=report.entity,
                label=constraint.label,
                description=(constraint.description or ''),
                violations=constraint.result_cnt,
                query_http_status=constraint.query_http_status,
                query_time=constraint.query_time,
                query_timeout=constraint.query_timeout,
#               sparql=constraint.sparql,  # do not include as this bloats the page size of the report page
                errors=error_str,
            )

    text += '{{/footer}}\n[[Category:Database reports|Complex Constraints]]'

    edit_page('Wikidata:Database reports/Complex constraints', text)
