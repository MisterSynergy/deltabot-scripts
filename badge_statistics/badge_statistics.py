#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0
import time
import pywikibot
import json
import requests

site = pywikibot.Site('wikidata','wikidata')

badges = ['Q17437798', 'Q17437796', 'Q17559452', 'Q17506997', 'Q17580674']
text = 'Update: <onlyinclude>{0}</onlyinclude>\n\n'.format(time.strftime("%Y-%m-%d %H:%M (%Z)"))

#create single rankings
for badge in badges:
    payload = {
        'query': 'SELECT ?item (count(*) as ?cnt) WHERE {	?article schema:about ?item . ?article  wikibase:badge wd:'+badge+' } GROUP BY ?item ORDER BY DESC(?cnt) LIMIT 20',
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    text += '== Top 20: {{Q|'+badge+'}} ==\n\n'
    text += '{| class="wikitable sortable"\n! Item !! {{Q|'+badge+'}}\n'
    data = r.json()
    for m in data['results']['bindings']:
        text += '|-\n| {{Q|'+m['item']['value'].replace('http://www.wikidata.org/entity/', '')+'}} || '+m['cnt']['value']+'\n'
    text += '|}\n\n'

#create total ranking    
payload = {
    'query': 'SELECT ?item (GROUP_CONCAT(?badge; separator=",") AS ?badges) (GROUP_CONCAT(?cnt; separator=",") AS ?counts) (sum(?cnt) AS ?sum){ { SELECT ?item ?badge (COUNT(*) AS ?cnt) WHERE { VALUES ?badge {wd:' + ' wd:'.join(badges)+'} ?article schema:about ?item . ?article  wikibase:badge ?badge .  } GROUP BY ?item ?badge } } GROUP BY ?item ORDER BY DESC(?sum) LIMIT 50',
    'format': 'json'
}
r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
text += '== Top 50: Overall ==\n\n'
text += '{| class="wikitable sortable"\n! Item '
for badge in badges:
    text += '!! {{Q|'+badge+'}} '
text += '!! total\n'

collec = []
data = r.json()
for m in data['results']['bindings']:
    q = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
    item = {'q':q}
    b = m['badges']['value'].split(',')
    c = m['counts']['value'].split(',')
    for i in range(len(b)):
        item[b[i].replace('http://www.wikidata.org/entity/', '')] = c[i]
    item['sum'] = m['sum']['value']
    collec.append(item)
for item in collec:
    text += '|-\n| {{Q|'+item['q']+'}} || '
    for badge in badges:
        text += str(item[badge]) if badge in item else '0'
        text +=' || '
    text += str(item['sum'])+'\n'

text += '|}\n\n[[Category:Wikidata statistics|Badge statistics]]'

page = pywikibot.Page(site,'User:Pasleim/Badge_statistics')
page.put(text.decode('UTF-8'),comment='upd',minorEdit=False)
