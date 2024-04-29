#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot as pwb
import re

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


def main() -> None:
    text = '<includeonly>{{#switch: {{{1}}}\n'
    for category in CATEGORIES:
        cnt = 0

        category_page = pwb.Page(SITE, f'Wikidata:Property proposal/{category}')
        category_page_content = category_page.get().split('</noinclude>')
        proposals = re.findall('{{Wikidata:Property proposal/(.*?)}}', category_page_content[1])

        if not proposals:
            text += f'| {category} = 0\n'
            continue

        for proposal in proposals:
            proposal_page = pwb.Page(SITE, f'Wikidata:Property proposal/{proposal}')

            if proposal_page.isRedirectPage():
                proposal_page = proposal_page.getRedirectTarget()

            if not proposal_page.exists():
                continue

            cnt += re.sub(r'(<!([^>]+)>)|\s|\n', '', proposal_page.get()).count('status=|')

        text += f'| {category} = {cnt}\n'

    text += '| #default = <strong class="error">invalid parameter <kbd>{{{1}}}</kbd></strong>\n}}</includeonly>'

    count_page = pwb.Page(SITE, 'Wikidata:Property proposal/count')
    count_page.text = text
    count_page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
