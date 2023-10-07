#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
from time import strftime

import mariadb
import pywikibot as pwb


class Replica:
    def __init__(self) -> None:
        self.connection = mariadb.connect(
            host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
            database='wikidatawiki_p',
            default_file=f'{expanduser("~")}/replica.my.cnf',
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.connection.close()


def get_data(project:str) -> str:
    query = "SELECT ga, COUNT(*) AS gap FROM (SELECT COUNT(ips_item_id) AS ga, ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id=%(project)s) GROUP BY ips_item_id) AS subquery GROUP BY ga"
    params = { 'project' : project }
    with Replica() as cur:
        cur.execute(query, params)
        result = cur.fetchall()

    collec = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0
    }
    total = 0
    avg = 0
    for row in result:
        if row.get('ga') == 1:
            collec[0] += row.get('gap')
        elif row.get('ga') == 2:
            collec[1] += row.get('gap')
        elif row.get('ga') <= 6:
            collec[2] += row.get('gap')
        elif row.get('ga') <= 11:
            collec[3] += row.get('gap')
        else:
            collec[4] += row.get('gap')
        total += row.get('gap')
        avg += row.get('gap')*(row.get('ga')-1)

    if total < 100:
        return ''

    avg_f = avg / total
    text = '|-\n'
    text += f'| {project} || {total:,} || {avg_f:4.1f}'
    for i in range(0, 5):
        text += f' || {collec[i]/total*100:4.1f}%'

    query = 'SELECT COUNT(*) AS count, CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id=%(project)s) AND ips_site_id<>%(project)s GROUP BY ips_site_id ORDER BY count DESC LIMIT 0,3'
    params = { 'project' : project }
    with Replica() as cur:
        cur.execute(query, params)
        result = cur.fetchall()

    for row in result:
        text += f' || {row.get("ips_site_id", "")} || {row.get("count", 0):,}'

    text += '\n'

    return text


def main():
    header = """{| class="wikitable sortable"
|-
! colspan=3 |
! colspan=5 | Items with sitelinks to # other projects
! colspan=6 | Top 3 linked projects
|-
! Project
! data-sort-type="number" | Total Items
! data-sort-type="number" | Avg # of sitelinks
! data-sort-type="number" | # 0
! data-sort-type="number" | # 1
! data-sort-type="number" | # 2–5
! data-sort-type="number" | # 6–10
! data-sort-type="number" | # >10
! 1<sup>st</sup>
! data-sort-type="number" | links
! 2<sup>nd</sup>
! data-sort-type="number" | links
! 3<sup>rd</sup>
! data-sort-type="number" | links
"""

    text  = f'Update: <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>.\n\n'

    queries = {
        'Wikipedia' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wiki" AND ips_site_id NOT IN ("metawiki", "wikidatawiki", "commonswiki", "specieswiki", "wikifunctionswiki", "mediawikiwiki", "outreachwiki", "wikimaniawiki", "sourceswiki") ORDER BY ips_site_id',
        'Wikisource' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikisource" OR ips_site_id="sourceswiki" ORDER BY ips_site_id',
        'Wiktionary' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wiktionary" ORDER BY ips_site_id',
        'Wikinews' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikinews" ORDER BY ips_site_id',
        'Wikiquote' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikiquote" ORDER BY ips_site_id',
        'Wikivoyage' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikivoyage" ORDER BY ips_site_id',
        'Wikibooks' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikibooks" ORDER BY ips_site_id',
        'Wikiversity' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE "%wikiversity" ORDER BY ips_site_id',
        'Special' : 'SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id IN ("metawiki", "commonswiki", "wikidatawiki", "specieswiki", "wikifunctionswiki", "mediawikiwiki", "outreachwiki", "wikimaniawiki") ORDER BY ips_site_id'
    }

    for project, query in queries.items():
        text += f"""== {project} ==
{header}"""

        with Replica() as cur:
            cur.execute(query)
            results = cur.fetchall()

        for row in results :
            text += get_data(row.get('ips_site_id'))

        text += '|}\n'

    text += '\n[[Category:Wikidata statistics]]'

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Connectivity')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
