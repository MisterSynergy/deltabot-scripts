#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time
from datetime import date, timedelta

site = pywikibot.Site('wikidata','wikidata')

header = 'A list of active bots during the last month without bot flag. Update: <onlyinclude>{0}</onlyinclude>\n\n{{| class="wikitable sortable" style="width:100%%; margin:auto;"\n|-\n! User !! Edits¹\n'

table_row = '|-\n| {{{{User|{0}}}}} || {1}\n'

footer = '|}\n\n¹edits in namespace 0 during the last 30 days\n[[Category:Database reports]]'

timestamp = date.today()-timedelta(days=30)
query1 = 'SELECT rc_user_text, COUNT(*) FROM recentchanges WHERE rc_bot=0 AND rc_namespace=0 AND rc_timestamp > '+timestamp.strftime('%Y%m%d000000')+' AND (rc_user_text LIKE "%bot" OR rc_user_text LIKE "%Bot") GROUP BY rc_user_text HAVING rc_user_text NOT IN (SELECT user_name FROM user JOIN user_groups ON user_id=ug_user WHERE ug_group="bot")'

def makeReport(db):
	cursor = db.cursor()
	cursor.execute(query1)
	text = ''
	for user, cnt in cursor:
		if not user == 'Paucabot' and not user == 'Reubot': #whitelist
			text += table_row.format(user,cnt)
	return text

def main():
	page = pywikibot.Page(site,'Wikidata:Database reports/Unauthorized bots')
	db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",db="wikidatawiki_p", read_default_file="replica.my.cnf")
	report = makeReport(db)
	text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer
	page.put(text.decode('UTF-8'),summary='Bot:Updating database report',minorEdit=False)

if __name__ == "__main__":
	main()
