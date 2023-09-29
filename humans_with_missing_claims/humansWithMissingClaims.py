#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json
import re
import time

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

missingProps = ['P21', 'P19', 'P569', 'P734', 'P735']

headers = {
'User-Agent': 'PLbot: [[ Wikidata:Database reports/Humans with missing claims]]'
}

def createSummay(counts):
    props = list(counts.keys())
    props.sort(key=lambda x: int(x[1:]))

    text = 'Update: <onlyinclude>'+time.strftime("%Y-%m-%d %H:%M (%Z)") + '</onlyinclude>\n\n{| class="wikitable sortable"\n! Id !! Property '
    for p2 in missingProps:
        text += '!! {{P|' + p2 + '}} '
    for p1 in props:
        text += '\n|-\n|data-sort-value=' + p1[1:] + '| [[Property:' + p1 + '|' + p1 + ']] || [[/' + p1 + '|{{label|' + p1 + '}}]]'
        for p2 in missingProps:
            if p2 in counts[p1]:
                text += ' || [[/' + p1 + '#' + p2 + '|' + str(counts[p1][p2]) + ']]'
            else:
                text += ' || -'
    text += '\n|}\n\nNew reports can be requested on [[/input]].\n[[Category:Database reports]]'
    page = pywikibot.Page(site, 'Wikidata:Database reports/Humans with missing claims')
    page.put(text, summary='upd', minorEdit=False)


def createReport(p1, results, counts):
    cnt = 0
    try:
        text = ''
        for p2 in missingProps:
            if p2 not in counts:
                continue
            text += '== <span id="' + p2 + '"></span> Missing {{P|' + p2 + '}} ==\n'
            text += 'count: ' + str(counts[p2]) + '\n\n'
            for q in results[p2]:
                cnt += 1
                if cnt < 2500:
                    text += '*{{Q|' + q + '}}\n'
                else:
                    text += '*[[' + q + ']]\n'
            if counts[p2] > 1000:
                skip = counts[p2]-1000
                text += str(skip) + ' records skipped\n'
        if text == '':
            return 0
        text +='__FORCETOC__'
        page = pywikibot.Page(site, 'Wikidata:Database reports/Humans with missing claims/' + p1)
        page.put(text, summary='report update for [[Property:' + p1 + ']]', minorEdit=False)
    except:
        pass


def createLists(props):
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    sparql = 'SELECT ?item WHERE {{ ?item  wdt:{0} ?foo1 . ?item wdt:P31 wd:Q5 . OPTIONAL {{ ?item wdt:{1} ?novalue }} FILTER (!BOUND(?novalue))}} ORDER BY ?item LIMIT 1000'
    sparql_count = 'SELECT (count(DISTINCT ?item) as ?cnt) WHERE {{ ?item  wdt:{0} ?foo1 . ?item wdt:P31 wd:Q5 . OPTIONAL {{ ?item wdt:{1} ?novalue }} FILTER (!BOUND(?novalue))}}'
    counts = {}
    countsAll = {}
    for p1 in props:
        results = {}
        counts[p1] = {}
        for p2 in missingProps:
            try:
                results[p2] = []
                payload1 = {
                    'query': sparql.format(p1, p2),
                    'format': 'json'
                }
                r1 = requests.get(url, params=payload1, timeout=65, headers=headers)
                data1 = r1.json()

                payload2 = {
                    'query': sparql_count.format(p1, p2),
                    'format': 'json'
                }
                r2 = requests.get(url, params=payload2, timeout=65, headers=headers)
                data2 = r2.json()

                for m in data1['results']['bindings']:
                    val = m['item']['value'].split('http://www.wikidata.org/entity/')
                    results[p2].append(val[1])
                counts[p1][p2] = int(data2['results']['bindings'][0]['cnt']['value'])
            except:
                pass
        if len(counts[p1]) > 0:
            createReport(p1, results, counts[p1])
    createSummay(counts)

def main():
    page = pywikibot.Page(site, 'Wikidata:Database reports/Humans with missing claims/input')
    input = page.get()
    lists = input.split('\n')
    props = []
    for m in lists:
        if m[0] != '#':
            if re.match('^P\d+$', m) != None:
                props.append(m)
    createLists(props)

if __name__ == "__main__":
    main()

