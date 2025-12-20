#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
import mariadb
import pywikibot
import re

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

db = mariadb.connect(host='wikidatawiki.analytics.db.svc.wikimedia.cloud', database='wikidatawiki_p', default_file=f'{expanduser("~")}/replica.my.cnf')

cur = db.cursor(dictionary=True)
cur.execute('SELECT CONVERT(rc_title USING utf8) AS rc_title, CONVERT(comment_text USING utf8) AS comment_text FROM recentchanges JOIN comment_recentchanges ON rc_comment_id=comment_id WHERE rc_namespace=0 AND HEX(comment_text) LIKE "%E2808F";')

for row in cur.fetchall():
    try:
        res = re.search(r'\[\[Property:(P\d+)\]\]', row.get('comment_text', ''))
        if not res:
            continue
        p = res.group(1)
        item = pywikibot.ItemPage(repo, row.get('rc_title', ''))
        item.get()
        if p in item.claims:
            for claim in item.claims[p]:
                if claim.type in ['string', 'url', 'external-id']:
                    value = claim.getTarget()
                    if u'\u200f' in value:
                        newvalue = value.replace(u'\u200f', '').strip()
                        claim.changeTarget(newvalue)
    except:
        pass
