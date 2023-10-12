#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time
import re

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

header = 'A list of {0} pages which were disconnected from Wikidata. Data as of <onlyinclude>{1}</onlyinclude>.\n\n'
header += '{{| class="wikitable sortable" style="width:100%%; margin:auto;"\n|-\n! Page !! Item !! Comment !! User !! Time\n'

table_row = '|-\n| [[:{0}:{1}]] || [[{2}]] || <nowiki>{3}</nowiki> || [[User:{4}|{4}]] || {5}\n'

footer = '|}\n\n[[Category:Database reports|removed sitelinks]]'

query1 = """SELECT page_title, rc_comment, rc_user_text, rc_timestamp, rc_params FROM page
    JOIN recentchanges ON page_title=rc_title AND rc_namespace=0 AND rc_type=5 AND rc_source='wb'
    LEFT JOIN page_props ON page_id=pp_page AND pp_propname='wikibase_item'
    WHERE page_namespace=0 AND page_is_redirect=0 AND pp_page IS NULL
    ORDER BY page_title ASC;"""


def makeReport(db, s):
    cursor = db.cursor()
    cursor.execute(query1.format(s+'wiki'))
    text = ''
    for page_title, rc_comment, rc_user_text, rc_timestamp, rc_params in cursor:
        if s+'wiki' in rc_params:
            time = rc_timestamp[0:4] + '-' + rc_timestamp[4:6] + '-' + rc_timestamp[6:8] + ' ' + rc_timestamp[8:10] + ':' + rc_timestamp[10:12]
            res = re.search('"(q\d+)"', rc_params)
            if res:
                qid = res.group(1).capitalize()
            else:
                qid = ''
            text += table_row.format(s, page_title.replace('_', ' '), qid, rc_comment, rc_user_text, time)
    return text


def main():
    for s in ['fa', 'nl', 'de', 'fr', 'pt', 'ru']:
        page = pywikibot.Page(site, 'Wikidata:Database reports/removed sitelinks/' + s + 'wiki')
        db = MySQLdb.connect(host=s+'wiki.analytics.db.svc.eqiad.wmflabs', db=s + 'wiki_p', read_default_file='~/replica.my.cnf')
        report = makeReport(db, s)
        text = header.format(s, time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
        page.put(text.decode('UTF-8'), comment='Bot:Updating database report', minorEdit=False)

if __name__ == "__main__":
    main()
