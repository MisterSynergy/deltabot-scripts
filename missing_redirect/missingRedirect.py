#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime, timedelta
from pathlib import Path
import re

import pywikibot
from pywikibot.data import api


SITE = pywikibot.Site('wikidata', 'wikidata')
SITE.login()
REPO = SITE.data_repository()

cat = pywikibot.Category(SITE, 'Category:Notability policy exemptions')
liste = list(cat.articles(recurse=5))


def merge(fromId,toId):
    fromItem = pywikibot.ItemPage(REPO,fromId)
    toItem = pywikibot.ItemPage(REPO,toId)
    fromItem.mergeInto(toItem, ignore_conflicts='description')
    clearItem(fromId)
    fromItem.set_redirect_target(toItem, force=True, save=True)

def clearItem(fromId):
    #get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=SITE, parameters=params)
    data = req.submit()
    #clear item
    params2 = {
        'action': 'wbeditentity',
        'id': fromId,
        'clear': 1,
        'data':'{}',
        'bot': 1,
        'summary': 'clearing item to prepare for redirect',
        'token': data['query']['tokens']['csrftoken']
    }
    req2 = api.Request(site=SITE, parameters=params2)
    data2 = req2.submit()

def main():
    time_file = Path.home() / 'jobs/missing_redirect/missingRedirect_time.dat'
    with open(time_file,'r') as file_handle:
        done_until_str = file_handle.read()
    
    old_time_str = (datetime.strptime(done_until_str, "%Y%m%d%H%M%S") \
        + timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")
    
    now = datetime.now()
    new_time = now - timedelta(minutes=10)
    new_time_str = new_time.strftime("%Y%m%d%H%M%S")
    rccontinue = old_time_str+'|0'
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': old_time_str,
            'rcend': new_time_str,
            'rcdir': 'newer',
            'rclimit' : 500,
            'rctype': 'edit',
            'rcnamespace':0,
            'rctoponly':1,
            'rccontinue':rccontinue
        }
        req = api.Request(site=SITE, parameters=params)
        data = req.submit()
        for m in data['query']['recentchanges']:
            timestamp = m['timestamp']
            if 'comment' in m:
                res = re.search('\/\* wbmergeitems-to:0\|\|(Q[0-9]+) \*\/', m['comment'])
                if res:
                    #ignore items in Category:Notability policy exemptions
                    for ll in liste:
                        if m['title'] == ll.title()[5:]:
                            continue
                    try:
                        merge(m['title'],res.group(1))
                    except:
                        pass
        if 'query-continue' in data:
            rccontinue = data['query-continue']['recentchanges']['rccontinue']
        else:
            break
    with open(time_file, 'w') as file_handle:
        file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))

if __name__ == '__main__':
    main()
