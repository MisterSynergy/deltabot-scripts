#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
import re
import datetime
from datetime import datetime, timedelta

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

text = 'The following items may not be notable according to [[WD:N]]. Feel free to remove false positives from the list.\n\n'

#scan old items
yesterday = datetime.now() - timedelta(days=1)
page = pywikibot.Page(site,'User:Pasleim/notability')
oldtext = page.get()
foo = oldtext.split('\n')
for line in foo:
    if '===' in line:
        date = line
    elif '{{Q|' in line:
        res2 = re.search(r'\{\{Q\|Q?([0-9]*)\}\}',line)
        if res2:
            q = res2.group(1)
            item = pywikibot.ItemPage(repo,'Q'+str(q))
            if item.isRedirectPage():
                continue
            if not item.exists():
                continue
            dict = item.get()
            if not len(dict['sitelinks']): #no sitelinks
                if len(dict['claims']) < 3: #0, 1 or 2 claims
                    if sum(1 for _ in item.backlinks(namespaces=0)) == 0: #no backlinks
                        nstat = len(dict['claims'])
                        if date:
                            text += date+'\n'
                            date = None
                        if nstat == 1:
                            text += '{{Q|'+str(q)+'}} (1 statement)<br />\n'
                        else:
                            text += '{{Q|'+str(q)+'}} ('+str(nstat)+' statements)<br />\n'

#check item from yesterday
date = yesterday.strftime("%Y%m%d")
date2 = yesterday.strftime("%Y-%m-%d")

check = 0
rccontinue = date+'000000|0'
while (1 == 1):
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rctype': 'new',
        'rcprop': 'title',
        'rcstart': date+'000000',
        'rcend': date+'235959',
        'rcdir': 'newer',
        'rclimit' : 500,
        'rcnamespace':0,
        'rcshow' : '!patrolled',
        'rccontinue':rccontinue
        }
    req = api.Request(site=site, parameters=params)
    data = req.submit()
    for m in data['query']['recentchanges']:
        try:
            q = m['title']
            item = pywikibot.ItemPage(repo,q)
            if item.isRedirectPage():
                continue
            if not item.exists():
                continue
            dict = item.get()
            if not len(dict['sitelinks']): #no sitelinks
                if len(dict['claims']) < 3: #0, 1 or 2 claims
                    if sum(1 for _ in item.backlinks(namespaces=0)) == 0: #no backlinks
                        nstat = len(dict['claims'])
                        if check == 0:
                            check = 1
                            text += '==='+date2+'===\n'
                        if nstat == 1:
                            text += '{{Q|'+str(q)+'}} (1 statement)<br />\n'
                        else:
                            text += '{{Q|'+str(q)+'}} ('+str(nstat)+' statements)<br />\n'
        except:
            pass
    if 'query-continue' in data:
        rccontinue = data['query-continue']['recentchanges']['rccontinue']
    else:
        break

page.put(text, summary='upd', minorEdit=False)
print('update successful')


