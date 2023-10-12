#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata','wikidata')

header = 'Update: <onlyinclude>{0}</onlyinclude>\n\n{{| class="wikitable sortable plainlinks"\n|-\n!Id !! Description !! Active Since !! Just Warned !! Edited !! Warning Deterred\n'
footer = '|}\n\n[[Category:Wikidata statistics]]'

table_row = '|-\n| [//wikidata.org/wiki/Special:AbuseLog?wpSearchFilter={0} {0}] || {1} || {2}-{3}-{4} || {5} || {6} || {7}%\n'

query1 = 'SELECT af_id, af_public_comments FROM abuse_filter WHERE af_actions="warn,tag"'
query2 = 'SELECT afh_timestamp FROM abuse_filter_history WHERE afh_changed_fields LIKE "%actions%" AND afh_filter={0} ORDER BY afh_timestamp DESC LIMIT 1'
query3 = 'SELECT count(*) FROM abuse_filter_log WHERE afl_filter={0} AND afl_actions="{1}" AND afl_timestamp>{2}'

def makeReport(db):
    text = ''
    cursor1 = db.cursor()
    cursor1.execute(query1)
    for af, comment in cursor1:
        cursor2 = db.cursor()
        af = int(af)
        cursor2.execute(query2.format(af))
        start = cursor2.fetchall()[0][0]
        cursor3 = db.cursor()
        cursor3.execute(query3.format(af,'warn',start))
        warn = cursor3.fetchall()[0][0]
        cursor4 = db.cursor()
        cursor4.execute(query3.format(af,'tag',start))
        tag = cursor4.fetchall()[0][0]
        if warn != 0:
            deterred = str(round((warn-tag)/float(warn)*100,1))
        else:
            deterred = '0'
        text += table_row.format(af,comment,start[0:4],start[4:6],start[6:8],warn-tag,tag,deterred)
    return text

def main():
    page = pywikibot.Page(site,'Wikidata:Database reports/Abuse filter effectiveness')
    db = MySQLdb.connect(host="wikidatawiki.labsdb",db="wikidatawiki_p", read_default_file="~/replica.my.cnf")
    report = makeReport(db)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text.decode('UTF-8'),comment='Bot:Updating database report',minorEdit=False)

if __name__ == "__main__":
    main()
