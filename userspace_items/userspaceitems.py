#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata','wikidata')

header = 'A list of pages with links to userspace. Update: <onlyinclude>{0}</onlyinclude>\n\n{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|- style="white-space:nowrap;"\n! Item !! Link\n'
footer = '|}\n\n[[Category:Wikidata statistics]]'

table_row = '|-\n| [[Q{0}]] || [[{1}:{2}:{3}]]\n'

query = """
SELECT
 ips_item_id,
 ips_site_page
FROM wb_items_per_site
WHERE ips_site_id="{site}"
AND ips_site_page LIKE "{ns}:%";
"""

def makeReport(db):
    text = ''
    f1 = open('reports/userspace_names.dat','r')
    for line in f1:
        row = line.strip().split('|')
        #if row[2] == 'simple': #whitelist simple wiki
        #    continue
        text+= get_report(db,*row)
    return text

def get_report(db, dbname, group, lang, ns):
    text = ''
    cursor = db.cursor()
    cursor.execute(query.format(site=dbname, ns=ns))
    for row in cursor:
        if 'Vorlage' in row[1] or 'Userbox' in row[1]: #whitelist userboxes
            continue
        text += table_row.format(row[0], group, lang, row[1])
    return text

def main():
    page = pywikibot.Page(site,'Wikidata:Database reports/User pages')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report = makeReport(db)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text.decode('UTF-8'),summary='Bot:Updating database report',minorEdit=False)    
    
if __name__ == "__main__":
    main()
