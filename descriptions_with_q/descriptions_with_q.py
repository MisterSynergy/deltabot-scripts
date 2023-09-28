#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import time
import pywikibot

site = pywikibot.Site('wikidata', 'wikidata')

header = 'Update: <onlyinclude>{0}</onlyinclude>.\n\n{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|-\n! item !! language !! description\n'
table_row = '|-\n| [[Q{}]] || {} || <nowiki>{}</nowiki>\n'
footer = '|}\n\n[[Category:Database reports]]'

query = "SELECT wbit_item_id as id, wbxl_language as language, wbx_text as text FROM wbt_item_terms LEFT JOIN wbt_term_in_lang ON wbit_term_in_lang_id = wbtl_id LEFT JOIN wbt_type ON wbtl_type_id = wby_id LEFT JOIN wbt_text_in_lang ON wbtl_text_in_lang_id = wbxl_id LEFT JOIN wbt_text ON wbxl_text_id = wbx_id WHERE wby_name = 'description' AND wbx_text REGEXP 'Q[1-9][0-9]{3}'"


def makeReport(db):
    cur = db.cursor()
    cur.execute(query)
    text = ''
    items = []
    for row in cur.fetchall():
        items.append([row[0], row[1], row[2]])
    items.sort(key=lambda x: x[0])
    for row in items:
        text += table_row.format(row[0], row[1].decode(), row[2].decode())
    return text


def main():
    page = pywikibot.Page(
        site, 'Wikidata:Database reports/Descriptions_with_Q')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report = makeReport(db)
    text = header.format(time.strftime(
        "%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text, summary='Bot:Updating database report', minorEdit=False)


if __name__ == "__main__":
    main()
