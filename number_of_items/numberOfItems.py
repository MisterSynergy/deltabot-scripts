#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot

db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
site = pywikibot.Site('wikidata','wikidata')

cur = db.cursor()
cur.execute('SELECT count(*) FROM page WHERE page_namespace=0 and page_is_redirect=0')
for row in cur.fetchall():
    page = pywikibot.Page(site,'Template:Numberofarticles')
    page.put(row[0], summary='upd',minorEdit=False)
