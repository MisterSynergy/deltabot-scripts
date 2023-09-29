# -*- coding: UTF-8 -*-
#licensed under CC0

import MySQLdb
import time
import pywikibot
import re

site = pywikibot.Site('wikidata','wikidata')

cnx = MySQLdb.connect(host="tools-db", db="s51591__main", read_default_file="replica.my.cnf")
cur = cnx.cursor()

page = pywikibot.Page(site, 'User:Pasleim/projectmerge-input')
content = page.get()
content = content.replace('-','_')
#find new entries
lists = content.split('\n')
for m in lists:
	if m == '':
		continue
	if m[0] != '#' and m[0] != '<':
		res = re.search(u'([a-z_]+)\s+([a-z_]+)',m)
		if res:
			wiki1 = res.group(1)
			wiki2 = res.group(2)
			cur.execute('SELECT id FROM merge_status WHERE wiki1="'+wiki1+'" AND wiki2="'+wiki2+'"')
			if cur.rowcount == 0:
				cur.execute('INSERT INTO merge_status (wiki1, wiki2, update_requested) VALUES ("'+wiki1+'","'+wiki2+'", NOW())')
				cnx.commit()
#find removed entries
cur.execute('SELECT id, wiki1, wiki2 FROM merge_status')
for row in cur.fetchall():
	if row[1]+' '+row[2] not in content:
		cur.execute('DELETE FROM merge_status WHERE id = "'+str(row[0])+'"')
		cnx.commit()

cur.close()
cnx.close()
