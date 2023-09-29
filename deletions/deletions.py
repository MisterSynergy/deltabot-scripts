#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata', 'wikidata')

header1 = '{{{{FULLPAGENAME}}/Header/{{#ifexist:{{FULLPAGENAME}}/Header/{{int:lang}}|{{int:lang}}|en}}}}\n'
header2 = 'Update: <onlyinclude>{0}</onlyinclude>.\n\n{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|-\n! {{{{int:userlogin-yourname}}}} !! {{{{int:deletionlog}}}}\n'

table_row = '|-\n| [[User:{0:s}|{0:s}]] || [{{{{fullurl:Special:Log/delete|user={1:s}}}}} {2:d}]\n'

footer = '|}\n\n[[Category:Wikidata statistics]]\n[[Category:Wikidata administrators]]'

query1 = 'SELECT actor_name, count(*) FROM logging JOIN actor ON log_actor = actor_id WHERE log_action="delete" AND actor_user IN (SELECT ug_user FROM user_groups WHERE ug_group="sysop") GROUP BY log_actor ORDER BY actor_name'

def makeReport(db):
    cursor = db.cursor()
    cursor.execute(query1)
    text = ''
    for user, cnt in cursor:
        text += table_row.format(user.decode(), user.decode().replace(' ', '_'), cnt)
    return text

def main():
    page = pywikibot.Page(site, 'Wikidata:Database reports/Deletions')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report = makeReport(db)
    text = header1 + header2.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
    page.put(text, summary='Bot:Updating database report', minorEdit=False)

if __name__ == "__main__":
    main()
