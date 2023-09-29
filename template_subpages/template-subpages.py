#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import time
import pywikibot

db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
cur.execute('SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE (ips_site_page LIKE "%/doc" OR ips_site_page LIKE "%/sandbox" OR ips_site_page LIKE "%/testcases" OR ips_site_page LIKE "%/TemplateData" OR ips_site_page LIKE "%/dok" OR ips_site_page LIKE "%/belge" OR ips_site_page LIKE "%/Spielwiese" OR ips_site_page LIKE "%/شرح") AND ips_site_page NOT LIKE "Wiki%"')
text = 'Found '+str(cur.rowcount)+' items\n\n'
text += '== Items with sitelinks /doc, /dok, /belge, /sandbox, /testcases, /TemplateData, /شرح ==\n'

for row in cur.fetchall():
    text += '*'+row[1]+': [[Q'+str(row[0])+']]\n'

#write to wikidata
site = pywikibot.Site('wikidata','wikidata')
page = pywikibot.Page(site,'User:Pasleim/Unsupported sitelinks')
page.put(text.decode('UTF-8'),summary='upd',minorEdit=False)
