#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import requests
import json
import pywikibot
import operator

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

exec(open('reports/implausible_coordinates_borders.dat').read())

text = '== Implausible Coordinate ==\n'

sorted_countries = sorted(countries.items(), key=operator.itemgetter(1))
for x in sorted_countries:
    q = x[0]
    country = x[1]
    try:
        c = 0
        payload = {
            'query': 'SELECT DISTINCT ?item WHERE { ?item wdt:P17 wd:Q'+str(q)+';p:P625/psv:P625 ?node . ?node wikibase:geoLatitude ?lat . ?node wikibase:geoLongitude ?lon . FILTER (?lon < '+str(west[country])+' || ?lon > '+str(east[country])+' || ?lat < '+str(south[country])+' || ?lat > '+str(north[country])+') OPTIONAL { ?item wdt:P17 ?c2 . FILTER (?c2 NOT IN (wd:Q'+str(q)+')) } FILTER (!bound(?c2)) }',
            'format': 'json'
        }
        r = requests.get('http://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
        data = r.json()
        for m in data['results']['bindings']:
            if c == 0:
                c = 1
                text += '\n=== ' + country + ' ===\n'
            text += '[['+m['item']['value'].replace('http://www.wikidata.org/entity/', '') + ']], '
    except:
        pass

site = pywikibot.Site('wikidata', 'wikidata')
page = pywikibot.Page(site, 'User:Pasleim/Implausible/coordinate')
page.put(text, summary='upd', minorEdit=False)
