#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata', 'wikidata')

header = 'Update: <onlyinclude>{0}</onlyinclude>\n==Items with the most links but without statements==\n{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|-\n! Item !! # links\n'
middle = '|}\n\n==Items with the most sitelinks but without statements==\n{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|-\n! Item !! # sitelinks\n'
footer = '|}\n\n[[Category:Database reports|Popular items without claims]]'
table_row = '|-\n| {{{{Q|{0}}}}} || {1}\n'

query1 = """SELECT pl_title, count(*) AS cnt FROM pagelinks
    WHERE pl_from_namespace=0 AND pl_namespace=0
    AND pl_title IN (
        SELECT page_title FROM page JOIN page_props ON page_id=pp_page
        WHERE pp_propname = "wb-claims" AND pp_value=0
    )
    GROUP BY pl_title
    ORDER BY cnt DESC
    LIMIT 100;"""

query2 = """SELECT page_title, ppsitelinks.pp_value FROM page_props AS ppclaims
    JOIN page ON ppclaims.pp_page=page_id AND page_namespace=0 AND page_is_redirect=0
    JOIN page_props AS ppsitelinks ON page_id=ppsitelinks.pp_page AND ppsitelinks.pp_propname='wb-sitelinks'
    WHERE ppclaims.pp_propname='wb-claims' AND ppclaims.pp_value=0
    ORDER BY CAST(ppsitelinks.pp_value AS int) DESC
    LIMIT 100;"""
  

def makeReport(db, query):
    cursor = db.cursor()
    cursor.execute(query)
    text = ''
    for val, cnt in cursor:
        text += table_row.format(val.decode(), cnt)
    return text


def main():
    page = pywikibot.Page(site, 'Wikidata:Database reports/Popular items without claims')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report1 = makeReport(db, query1)
    report2 = makeReport(db, query2)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report1 + middle + report2 + footer
    page.put(text, summary='Bot:Updating database report', minorEdit=False)

if __name__ == "__main__":
    main()
