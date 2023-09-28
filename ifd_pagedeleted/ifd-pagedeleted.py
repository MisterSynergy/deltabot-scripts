#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import sys
import pywikibot
from pywikibot.data import api
import re
from os.path import expanduser

sys.tracebacklimit = 0

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()
page = pywikibot.Page(site, 'User:Pasleim/Items for deletion/Page deleted')

text = ''

prefixDic = {'quote':'q', 'news': 'n', 'voyage': 'voy', 'books': 'b', 'source': 's', 'species': 'species', 'versity': 'v', 'media': 'wmf', 'data': 'd'}

ts_filename = f'{expanduser("~")}/jobs/ifd_pagedeleted/ifd-pagedeleted_time.dat'

def countEid(cc):
    cnt = 0
    for key in cc:
        if cc[key][0].type == 'external-id':
           cnt += 1
    return cnt

def oldEdits():
    global text
    oldtext = page.get()
    foo = oldtext.split('\n')
    for line in foo:
        if '|}' not in line:
            text += line+'\n'

def newEdits():
    global text
    f1 = open(ts_filename,'r')
    oldTime = f1.read().strip()
    rccontinue = oldTime+'|0'
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': oldTime,
            'rcdir': 'newer',
            'rctype': 'edit',
            'rcnamespace': 0,
            'rccontinue': rccontinue,
            'rclimit': 500,
            'format': 'json'
        }
        req = api.Request(site=site, parameters=params)
        data = req.submit()
        for m in data['query']['recentchanges']:
            timestamp = m['timestamp']
            if 'comment' not in m:
                continue
            res = re.search('clientsitelink-remove\:1\|\|(.*)wiki(.*) \*\/ (.*)', m['comment'])
            if res:
                try:
                    item = pywikibot.ItemPage(repo, m['title'])
                    if item.isRedirectPage():
                        continue
                    if not item.exists():
                        continue
                    dict = item.get()
                    if len(dict['sitelinks']) != 0:
                        continue
                    nstat = len(dict['claims'])
                    nsources = 0
                    for p in dict['claims']:
                        for c in dict['claims'][p]:
                            for s in c.getSources():
                                keys = list(s.keys())
                                nsources += len(keys) - keys.count('P143')
                    source = '' if nsources == 0 else '<small>(' + str(nsources) + ')</small>'
                    backlinks = sum(1 for _ in item.backlinks(namespaces=0))
                    externalids = countEid(dict['claims'])
                    if res.group(2) == None or res.group(2) == '':
                        prefix = 'w'
                    else:
                        prefix = prefixDic[res.group(2)]
                    text += u'|-\n| {{Q|'+m['title']+'}} ([//www.wikidata.org/w/index.php?title='+m['title']+'&action=history hist]) || '+str(nstat)+' '+source+' || '+str(backlinks)+' || '+str(externalids)+' || [[:'+prefix+':'+res.group(1).replace('_','-')+':'+res.group(3)+']] || '+m['timestamp']+'\n'
                except:
                    pass
        if 'query-continue' in data:
             rccontinue = data['query-continue']['recentchanges']['rccontinue']
        else:
             break
    text += '|}'
    f3 = open(ts_filename,'w')
    f3.write(re.sub(r'\:|\-|Z|T', '', timestamp))
    f3.close()
    page.put(text, summary='upd', minorEdit=False)

if __name__ == "__main__":
    oldEdits()
    newEdits()
