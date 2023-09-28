#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import time
import pywikibot
import requests
import json

site = pywikibot.Site('wikidata','wikidata')

def make_report(pr):
    text = 'Many wikipedia have these articles. Please create these articles in [[:%s:|%s wikipedia]]. Update: <onlyinclude>%s</onlyinclude>\n' % (pr,pr,time.strftime("%Y-%m-%d %H:%M (%Z)").encode('utf-8'))
    cnt = 0

    payload = {
                'query': """SELECT ?item ?cnt WHERE {
          {
        SELECT ?item (count(*) as ?cnt)
        WHERE
        {
            ?item wdt:P106 wd:Q937857;
                  ^schema:about ?article
        } GROUP BY ?item order by desc(?cnt)
        }
        filter not exists{?item ^schema:about/schema:isPartOf <https://"""+pr+""".wikipedia.org/> .}
        } ORDER BY DESC(?cnt) LIMIT 100 """,
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    for m in data['results']['bindings']:
        q = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        
        if m['cnt']['value'] != cnt:
            cnt = m['cnt']['value']
            text += '\n=='+str(cnt)+' wikipedia==\n'
        text += '*{{Q|'+q+'}}\n'
    text += '\n[[Category:WikiProject Association football/Wanted footballers]]'

    #write to wikidata
    page = pywikibot.Page(site, 'Wikidata:WikiProject Association football/Wanted footballers/{}'.format(pr))
    page.put(text, summary='Bot:Updating database report', minorEdit=False)

def main():
    projects = ["en","sv","nl","de","fr","war","ceb","ru","it","es","vi","pl","ja","pt","zh","uk","ca","fa","no","fi","id","ar","sr","cs","ko","sh","hu","ms","ro","tr"]
    for pr in projects:
        try:
            make_report(pr)
        except:
            pass

if __name__ == "__main__":
    main()
