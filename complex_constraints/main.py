#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import sys
import pywikibot as pwb

from cc.PageWithComplexConstraintDefinition import PageWithComplexConstraintDefinition, TEMPLATE
from cc.utils import write_overview
from cc.bot import SITE


def process_one_report(entity:str) -> None:
    if entity.startswith('P'):
        page = pwb.Page(SITE, f'Property_talk:{entity}')
    else:
        page = pwb.Page(SITE, f'Talk:{entity}')

    report = PageWithComplexConstraintDefinition(page)
    report.evaluate_constraints()
    report.write_constraint_report()


def process_all_reports() -> None:
    template_page = pwb.Page(SITE, f'Template:{TEMPLATE}')

    gen = template_page.getReferences(
        only_template_inclusion=True,
        namespaces=[1, 121],  # Talk and Property_talk
        content=True
    )

    reports:list[PageWithComplexConstraintDefinition] = []

    for page in gen:
        report = PageWithComplexConstraintDefinition(page)
        report.evaluate_constraints()
        report.write_constraint_report()
        reports.append(report)

    write_overview(reports)


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1][0] in [ 'P', 'Q' ]:
        process_one_report(sys.argv[1])
    else:
        process_all_reports()


if __name__ == '__main__':
    main()
