#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import sys
import pywikibot
from pywikibot.data import api
import re
import requests

sys.tracebacklimit = 0

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

prefixDic = {'quote':'q', 'news': 'n', 'voyage': 'voy', 'books': 'b', 'source': 's', 'species': 'species', 'versity': 'v', 'media': 'wmf', 'data': 'd'}

def countEid(cc):
    cnt = 0
    for key in cc:
        if cc[key][0].type == 'external-id': 
           cnt += 1
    return cnt

def oldEdits(title):
    text = '{{User:Pasleim/Items for deletion/archivebox-pagedeleted}}\n'
    text += 'The following items may no longer be notable according to [[WD:N]]. Feel free to remove false positives from the list.\n\n'
    text += '{| class="wikitable sortable plainlinks"\n! Item !! # Claims<br /><small>(# sources)</small> !! # Backlinks !! # ext-Id !! Last deleted page !! Timestamp \n'
    page = pywikibot.Page(site,title) 
    oldtext = page.get()
    foo = oldtext.split('\n')
    for line in foo:
        res = re.search(r'{{Q\|(Q[0-9]+)}} (.*) \|\| (.*) \|\| ([0-9]+) \|\| ([0-9]+) \|\| (.*)', line)
        if res:
            q = res.group(1)
            item = pywikibot.ItemPage(repo,q)
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
            source = '' if nsources == 0 else ' <small>(' + str(nsources) + ')</small>'
            backlinks = sum(1 for _ in item.backlinks(namespaces=0))
            externalids = countEid(dict['claims'])
            text += u'|-\n| {{Q|'+res.group(1)+'}} '+res.group(2)+' || '+str(nstat)+source+' || '+str(backlinks)+' || '+str(externalids)+' || '+res.group(6)+'\n' 
    text += '|}'


    page.put(text, summary='upd', minorEdit=False)

def main():
    payload = {
        'action': 'query',
        'list': 'allpages',
        'apprefix': 'Pasleim/Items for deletion/Page deleted',
        'aplimit': 120,
        'apnamespace': 2,
        'format': 'json'
    }
    r = requests.get('https://www.wikidata.org/w/api.php',params=payload)
    data = r.json()
    for m in data['query']['allpages']:
        #try:
        oldEdits(m['title'])
        #except:
        #    print('error with '+m['title'])
                
if __name__ == "__main__":
    main()
