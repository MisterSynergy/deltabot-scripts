#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata','wikidata')

header = 'A list of items with the most sitelinks. Data as of <onlyinclude>{0}</onlyinclude>.\n\n{{| class="wikitable sortable" style="width:100%%; margin:auto;"\n|-\n! Item !! Sitelinks\n'

table_row = '|-\n| {{{{Q|{0}}}}} || {1}\n'

footer = '|}\n\n[[Category:Wikidata statistics|Most sitelinked items]] [[Category:Database reports|Most sitelinked items]]'

query1 = 'SELECT ips_item_id, count(*) AS cnt FROM wb_items_per_site GROUP BY ips_item_id ORDER BY cnt DESC LIMIT 100'

def makeReport(db):
    cursor = db.cursor()
    cursor.execute(query1)
    text = ''
    for item, cnt in cursor:
        text += table_row.format(item,cnt)
    return text

def main():
    page = pywikibot.Page(site,'Wikidata:Database reports/Most sitelinked items')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report = makeReport(db)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text, summary='Bot:Updating database report', minorEdit=False)

if __name__ == "__main__":
    main()

