#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from dataclasses import dataclass, field
from time import strftime

import mwparserfromhell as mwparser
import pywikibot as pwb

from .ComplexConstraint import ComplexConstraint
from .bot import edit_page


TEMPLATE = 'Complex constraint'


@dataclass
class PageWithComplexConstraintDefinition:
    page:pwb.Page
    constraints:list[ComplexConstraint] = field(default_factory=list)

    entity:str = field(init=False)


    def __post_init__(self) -> None:
        self.entity = self.page.title().split(':')[1]  # page is in Talk: or Property_talk: namespace
        self._parse_templates_on_page()


    def _parse_templates_on_page(self) -> None:
        wikitext = mwparser.parse(self.page.get())

        for template in wikitext.filter_templates():
            if template.name.strip() != TEMPLATE:
                continue

            self.constraints.append(ComplexConstraint(template))


    def evaluate_constraints(self) -> None:
        for constraint in self.constraints:
            constraint.evaluate()


    def write_constraint_report(self) -> None:
        text = f'{{{{Complex constraint violations report|date={strftime("%Y-%m-%d %H:%M (%Z)")}}}}}\n'

        q_template_cnt = 0

        for constraint in self.constraints:
            constraint_text, q_template_cnt = constraint.write_section_for_constraint_violation_report(q_template_cnt)
            text += constraint_text

        edit_page(f'Wikidata:Database reports/Complex constraint violations/{self.entity}', text)
