#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json

site = pywikibot.Site('wikidata','wikidata')

def candByImage():
    payload = {
        'query': """SELECT DISTINCT ?item ?item2 WHERE {
                  ?item wdt:P31/wdt:P279* wd:Q3305213 . 
                  ?item2 wdt:P31/wdt:P279* wd:Q3305213 . 
                  ?item wdt:P18 ?image .
                  ?item2 wdt:P18 ?image
                  FILTER(?item != ?item2 && str(?item) < str(?item2))
                  } ORDER BY str(?item) LIMIT 500""",
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    text = ''
    for m in data['results']['bindings']:
        item = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        item2 = m['item2']['value'].replace('http://www.wikidata.org/entity/', '')
        text += '*{{Q|'+item+'}}, {{Q|'+item2+'}}\n'
    return text


def candByQualifier(ps, pq):
    payload = {
        'query': """SELECT DISTINCT ?item1 ?item2 WHERE {{
                  ?item1 wdt:P31/wdt:P279* wd:Q3305213 .   
                  ?item1 p:{0} ?statement1 .
                  ?statement1 ps:{0} ?value;
                              pq:{1} ?qvalue1 .
                  ?item2 wdt:P31/wdt:P279* wd:Q3305213 .   
                  ?item2 p:{0} ?statement2 .
                  ?statement2 ps:{0} ?value;
                              pq:{1} ?qvalue2 .
                  FILTER(str(?item1) < str(?item2))
                  FILTER(?qvalue1 = ?qvalue2)
                  }} ORDER BY str(?item1) LIMIT 500
                """.format(ps, pq),
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    text = ''
    for m in data['results']['bindings']:
        item1 = m['item1']['value'].replace('http://www.wikidata.org/entity/', '')
        item2 = m['item2']['value'].replace('http://www.wikidata.org/entity/', '')
        text += '*{{Q|'+item1+'}}, {{Q|'+item2+'}}\n'
    return text


def main():
    mtext = '__TOC__\n== Items with same inventory number of the same collection ==\n\n'
    mtext += candByQualifier('P217', 'P195')
    mtext += '\n== Items with same catalog code of the same catalog ==\n\n'
    mtext += candByQualifier('P528', 'P972')    
    mtext += '\n== Paintings with same image ==\n\n'
    mtext += candByImage()
    mtext += '\n[[Category:WikiProject sum of all paintings|Duplicate paintings]]\n[[Category:Database reports|Duplicate paintings]]\n[[Category:Merge candidates|Duplicate paintings]]'

    page = pywikibot.Page(site, 'Wikidata:WikiProject sum of all paintings/Duplicate paintings')
    page.put(mtext, summary='upd', minorEdit=False)

if __name__ == "__main__":
    main()
