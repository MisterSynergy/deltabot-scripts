#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata','wikidata')
repo = site.data_repository()

header = 'A list of the most linked disambiguation page items. Data as of <onlyinclude>{0}</onlyinclude>.\n\n{{| class="wikitable sortable" style="width:100%%; margin:auto;"\n|-\n! Item !! Usage\n'

table_row = '|-\n| {{{{Q|{0}}}}} || {1}\n'

footer = '|}\n\n[[Category:Wikidata statistics]]'

query1 = 'SELECT pl_title, COUNT(*) AS cnt FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_title IN (SELECT page_title FROM page JOIN pagelinks ON page_id=pl_from WHERE pl_title="Q4167410") AND pl_from NOT IN (SELECT page_id FROM page WHERE page_is_redirect = 1) GROUP BY pl_title ORDER BY cnt DESC LIMIT 200'

def makeReport(db):
    cursor = db.cursor()
    cursor.execute(query1)
    text = ''
    for item, cnt in cursor:
        print(item)
        itempage = pywikibot.ItemPage(repo, item)
        itempage.get()
        if 'P31' in itempage.claims:
            for m in itempage.claims['P31']:
                if m.getTarget().getID() == 'Q4167410':
                    text += table_row.format(item,cnt)
    return text

def main():
    page = pywikibot.Page(site,'Wikidata:Database reports/Most linked disambiguation page items')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="~/replica.my.cnf")
    report = makeReport(db)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text.decode('UTF-8'),comment='Bot:Updating database report',minorEdit=False)

if __name__ == "__main__":
    main()