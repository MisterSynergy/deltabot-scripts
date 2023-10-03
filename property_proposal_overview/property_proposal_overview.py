#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime
import re

import pywikibot as pwb


SITE = pwb.Site('wikidata', 'wikidata')
CATEGORIES = [
    'Generic',
    'Place',
    'Authority control',
    'Creative work',
    'Transportation',
    'Person',
    'Natural science',
    'Organization',
    'Sister projects',
    'Sports',
    'Lexemes',
    'Computing',
]


def create_overview(proposals:dict[str, tuple[str, list[str], int, int]]) -> None:
    proposals_value = [ value for _, value in proposals.items() ]
    proposals_value.sort(key=lambda x:x[2])

    text = f"""Open proposals: {len(proposals_value)}

== All open property proposals ==
{{| class="wikitable sortable"
|-
! Proposal !! Category !! Days open !! Days since last edit
"""

    for proposal in proposals_value:
        title, categories, age, lastedit = proposal

        if age < 7:
            style = ''
        elif age < 14:
            style = f'style="background-color:#F8E0E0"'
        elif age < 31:
            style = f'style="background-color:#F6CECE"'
        else:
            style = f'style="background-color:#F5A9A9"'

        text += f"""|- {style}
| [[Wikidata:Property proposal/{title}|{title}]] || {', '.join(categories)} || {age} || {lastedit}
"""

    text += """|}
[[Category:Property proposals|Overview]]"""

    page = pwb.Page(SITE, 'Wikidata:Property proposal/Overview')
    page.text = text
    page.save(summary='upd', minor=False)


def main() -> None:
    today = datetime.today()
    all:dict[str, tuple[str, list[str], int, int]] = {}

    for category in CATEGORIES:
        page = pwb.Page(SITE, f'Wikidata:Property proposal/{category}')
        page_content = page.get()

        proposals = re.findall('{{Wikidata:Property proposal/(.*?)}}', page_content.replace('_',' '))
        for proposal in proposals:
            if proposal.lower().startswith('header/'):
                continue

            proposal_page = pwb.Page(SITE, f'Wikidata:Property proposal/{proposal}')

            if not proposal_page.exists():
                continue

            if proposal_page.isRedirectPage():
                proposal_page = proposal_page.getRedirectTarget()
                proposal = proposal_page.title()[len('Wikidata:Property proposal/'):]

            text = re.sub(r'(<!([^>]+)>)|\s|\n', '', proposal_page.get())
            if text.count('status=|') == 0 and text.count('status=ready|') == 0:
                continue

            history = [ rev for rev in proposal_page.revisions() ]

            if proposal not in all:
                data = (
                    proposal,
                    [ category ],
                    (today - history[-1].timestamp).days,
                    (today - history[0].timestamp).days
                )
                all[proposal] = data
            else:
                all[proposal][1].append(category)

    create_overview(all)


if __name__=='__main__':
    main()
