#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time
import requests

site = pywikibot.Site('wikidata','wikidata')

header = 'Update: <onlyinclude>{0}</onlyinclude>\n{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|-\n! Entity !! count !! deleted by\n'
footer = '|}\n\n[[Category:Database reports|Deleted Wikidata entities that are still linked]]'
table_row = '|-\n| {{{{{0}|{1}}}}} || [{{{{fullurl:Special:WhatLinksHere/{1}}}}} {2}] || [[User:{3}]]\n'

query = 'SELECT pl_title, COUNT(*) FROM pagelinks LEFT JOIN page ON pl_title = page_title AND pl_namespace = page_namespace WHERE (pl_from_namespace = 0 OR pl_from_namespace = 120) AND (pl_namespace = 0 OR pl_namespace = 120)    AND page_id IS NULL GROUP BY pl_title ORDER BY COUNT(*) DESC, pl_namespace, pl_title'


def makeReport(db, query):
    cursor = db.cursor()
    cursor.execute(query)
    text = ''
    for val, cnt in cursor:
        val = val.decode(encoding='utf-8')
        r = requests.get('https://www.wikidata.org/w/api.php?action=query&list=logevents&leprop=user|type&letitle={0}&format=json'.format(val))
        data = r.json()
        user = ''
        for m in data['query']['logevents']:
            if m['type'] == 'delete' and m['action'] == 'delete':
                user = m['user']
                break
        text += table_row.format(val[0], val, ('{:,}'.format(cnt)), user)
    return text

def main():
    page = pywikibot.Page(site, 'Wikidata:Database reports/Deleted Wikidata entities that are still linked')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report = makeReport(db, query)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text, summary='Bot:Updating database report',minorEdit=False)

if __name__ == "__main__":
    main()
