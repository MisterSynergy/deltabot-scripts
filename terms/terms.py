#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import time
import pywikibot

db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
cur.execute("SELECT count(*) FROM page WHERE page_namespace = 0 AND page_is_redirect=0")
blo =  cur.fetchall()
total =  blo[0][0]

text = 'Update: <onlyinclude>'+time.strftime("%Y-%m-%d %H:%M (%Z)")+'</onlyinclude>.\n\n'
text += 'Total items: '+('{:,}'.format(total))+'\n\n'
text += '== Number of labels, descriptions and aliases for items per language ==\n'
text += '{| class="wikitable sortable"\n|-\n! Language code\n! Language (English)\n! Language (native)\n! data-sort-type="number"|# of labels\n! data-sort-type="number"|# of descriptions\n! data-sort-type="number"|# of aliases\n! data-sort-type="number"|# of items with aliases\n'

collect = {}

#get languages
db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
cur.execute("SELECT DISTINCT term_language FROM wb_terms")
for row in cur.fetchall():
    collect[row[0]] = {}


#get labels
db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
for lang in collect:
    cur.execute("SELECT count(*) FROM wb_terms WHERE term_entity_type = 'item' AND term_type='label' AND term_language = '"+lang+"'")
    for row in cur.fetchall():
        collect[lang]['label'] = row[0]

#get descriptions
db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
for lang in collect:
    cur.execute("SELECT count(*) FROM wb_terms WHERE term_entity_type = 'item' AND term_type='description' AND term_language = '"+lang+"'")
    for row in cur.fetchall():
        collect[lang]['description'] = row[0]

#get aliases
db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()
for lang in collect:
    cur.execute("SELECT count(*), count(distinct(term_entity_id)) FROM wb_terms WHERE term_entity_type = 'item' AND term_type='alias' AND term_language='"+lang+"'")
    for row in cur.fetchall():
        collect[lang]['alias'] = row[0]
        collect[lang]['itemsWithAlias'] = row[1]


for lang in sorted(collect):
    text += '|-\n| '+lang+' || {{#language:'+lang+'|en}} || {{#language:'+lang+'}}\n| '
    if 'label' in collect[lang]:
        text += ('{:,}'.format(collect[lang]['label']))+' ('+str(round(100/(float)(total)*collect[lang]['label'],1))+'%)'
    text += ' || '
    if 'description' in collect[lang]:
        text += ('{:,}'.format(collect[lang]['description']))+' ('+str(round(100/(float)(total)*collect[lang]['description'],1))+'%)'
    text += '\n| '
    if 'alias' in collect[lang]:
        text += ('{:,}'.format(collect[lang]['alias']))+' || '+('{:,}'.format(collect[lang]['itemsWithAlias']))
    else:
        text += ' || '
    text += '\n'
text += '|}\n\n[[Category:Wikidata statistics|Language statistics]]'

#write to wikidata
if len(text) > 1000:
    site = pywikibot.Site('wikidata', 'wikidata')
    page = pywikibot.Page(site, 'User:Pasleim/Language statistics for items')
    page.put(text.decode('utf-8'), summary='upd', minorEdit=False)
