#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

#providing a list with unique violations, the script looks for merge candidates. Preferable, the list should only contains items from the same namespace

from os.path import expanduser
import re
from typing import Generator

import mariadb
import pywikibot as pwb


SITE = pwb.Site('wikidata','wikidata')

PROPERTIES = [ 'P301', 'P94', 'P41', 'P646', 'P494', 'P229', 'P225', 'P910', 'P685', 'P442', 'P1566' ]


def get_items(db, prop:str) -> Generator[tuple[str, str, str], None, None]:
    page = pwb.Page(SITE, f'Wikidata:Database_reports/Constraint violations/{prop}')
    text = page.get()

    res = re.search(r'== "Unique value" violations ==([^=]+)', text)
    if not res:
        return

    cur = db.cursor(dictionary=True)
    for line in res.group(1).split('\n'):
        line = line.strip()
        if ': [[Q' not in line:
            continue

        parts = line.split(': ')
        elements = parts[1].split(', ')

        for i in range(0, len(elements)-1):
            for j in range(i+1, len(elements)):
                query = """SELECT
                    a.ips_site_id
                FROM
                    wb_items_per_site AS a
                        INNER JOIN wb_items_per_site AS b ON a.ips_site_id=b.ips_site_id
                WHERE
                    a.ips_item_id=%(qid1)s
                    AND b.ips_item_id=%(qid2)s"""

                params = { 'qid1' : elements[i][3:-2], 'qid2' : elements[j][3:-2] }

                cur.execute(query, params)
                if cur.rowcount==0:
                    yield (elements[i][3:-2], elements[j][3:-2], parts[0])

    cur.close()


def update_list(db, prop:str, whitelist:list[tuple[int, int]]) -> None:
    gen = get_items(db, prop)
    if gen is None:
        return

    pretext = ''
    accepted = 0
    excluded = 0
    for row in gen:
        if [row[0], row[1]] in whitelist or [row[1], row[0]] in whitelist:
            excluded+=1
        else:
            accepted+=1
            if accepted < 5000:
                pretext += f'{row[2]}: {{{{Q|{row[0]}}}}}, {{{{Q|{row[1]}}}}}\n'

    #write text
    text = f'Merge candidates based on same {{{{P|{prop}}}}} value.\n\n'
    text += f'Found {excluded+accepted} merge candiates, excluding {excluded} candidates from the [[Wikidata:Do not merge|whitelist]] leads to {accepted} remaining candidates.\n\n'

    if accepted>0:
        text += f'== Merge candidates ==\n{pretext}'

    if accepted > 5000:
        skipped = accepted-5000
        text += f'\nSkipping {skipped} records\n'

    #write to wikidata
    page = pwb.Page(SITE, f'User:Pasleim/uniquemerge/{prop}')
    page.text = text
    page.save(summary='upd', minor=False)


def get_whitelist() -> list[tuple[int, int]]:
    #create whitelist
    page = pwb.Page(SITE, 'Wikidata:Do not merge')
    text = page.get()

    whitelist = []
    for match in re.findall(r'Q(\d+)(.*)Q(\d+)', text):
        whitelist.append(
            (
                int(match[0]),
                int(match[2]),
            )
        )

    return whitelist


def main() -> None:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf'
    )
    
    whitelist = get_whitelist()
    for prop in PROPERTIES:
        update_list(db, prop, whitelist)


if __name__ == '__main__':
    main()
