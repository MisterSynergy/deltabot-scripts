#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json
from pywikibot.exceptions import SpamblacklistError

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()


def getValue(datavalue, urlformatter):
    if type(datavalue) == pywikibot.ItemPage or type(datavalue) == pywikibot.PropertyPage:
        return datavalue.getID()
    elif type(datavalue) == pywikibot.WbQuantity:
        if datavalue.unit == '1':
            return str(datavalue.amount)
        else:
            return str(datavalue.amount) + ' {{label|' + datavalue.unit[31:] + '}}'
    elif type(datavalue) == pywikibot.FilePage:
        return datavalue.title()[5:]
    elif type(datavalue) == pywikibot.WbTime:
        if datavalue.precision == 11:
            return '{:04d}-{:02d}-{:02d}'.format(datavalue.year, datavalue.month, datavalue.day)
        elif datavalue.precision == 10:
            return '{:04d}-{:02d}'.format(datavalue.year, datavalue.month)
        else:
            return '{:04d}'.format(datavalue.year)
    elif type(datavalue) == pywikibot.Coordinate:
        return '{:7.4f}/{:7.4f}'.format(datavalue.lat, datavalue.lon)
    elif type(datavalue) == pywikibot.WbMonolingualText:
        return datavalue.text + '(' + datavalue.language + ')'
    elif 'id'in datavalue:
        return datavalue['id']
    else:
        if urlformatter:
            datavalue = '[' + urlformatter.replace('$1', datavalue) + ' ' + datavalue + ']'
        return str(datavalue)

def createSection(q, title, rel):
    text = u'{{List of properties/Header}}\n'
    payload = {
        'query': """SELECT DISTINCT ?prop ?datatype ?pair_num WHERE {{ ?prop {0} wd:{1}; wikibase:propertyType ?datatype
                      OPTIONAL {{
                        ?prop wdt:P1696 ?pair .
                        BIND(substr(str(?pair), 33) as ?pair_num)
                      }}
                    }} ORDER BY xsd:integer(substr(str(?prop), 33))""".format(rel, q),
        'format': 'json'
    }    
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    try:
        data = r.json() 
    except:
        return ''
    if len(data['results']['bindings']) == 0:
        return ''
    if len(data['results']['bindings']) > 1000 and title.count('/') <=1:
        item = pywikibot.ItemPage(repo, q)
        item.get()
        if 'P1269' in item.claims:
            sublabel1 = item.claims['P1269'][0].getTarget().get()['labels']['en']
            if sublabel1 in title and len(item.claims['P1269']) > 1:
                title += '/' + item.claims['P1269'][1].getTarget().get()['labels']['en']
            else:
                title += '/' + sublabel1
        else:
            title += '/' + item.labels['en']
        createCatPage(title, q)
        return "''see [[Wikidata:List of properties/" + title + "]]''\n\n"
        
    for m in data['results']['bindings']:
        pid = m['prop']['value'].replace('http://www.wikidata.org/entity/', '')
        if pid[0] != 'P':
            continue
        if pid in ['P5267', 'P5540']:
            continue # Wikimedia spam black list
        datatype = m['datatype']['value'][26:].lower()
        pair = m['pair_num']['value'] if 'pair_num' in m else ''
        proppage = pywikibot.PropertyPage(repo, pid)
        proppage.get()
        try:
            subject = proppage.claims['P1855'][0].getTarget().getID()
            object = proppage.claims['P1855'][0].qualifiers[pid][0].getTarget()
            if 'P1630' in proppage.claims:
                urlformatter = proppage.claims['P1630'][0].getTarget()
            else:
                urlformatter = False
            objectvalue = getValue(object, urlformatter)
            text += '{{{{List of properties/Row|id={0}|example-subject={1}|example-object={2}|pair={3}|datatype={4}|noexpensivecalls=1}}}}\n'.format(pid[1:], subject, objectvalue, pair, datatype)
        except:
            text += '{{{{List of properties/Row|id={0}|pair={1}|datatype={2}|noexpensivecalls=1}}}}\n'.format(pid[1:], pair, datatype)
    text += '{{Template:List_of_properties/Footer}}\n\n'
    return text
                
def createCatPage(title, q):
    print(title)
    payload = {
        'query': 'SELECT ?item WHERE {{ ?item wdt:P279 wd:{0}}} ORDER BY xsd:integer(substr(str(?item), 33))'.format(q),
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()    
    text = u'{{{{Q|{0}}}}}\n'.format(q)
    if len(data['results']['bindings']) > 0:
        for m in data['results']['bindings']:
            qsec = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
            text += u'=== {{{{label|{0}}}}} ===\n'.format(qsec)
            text += createSection(qsec, title, 'wdt:P31/wdt:P279*')
        other = createSection(q, title, 'wdt:P31')
        if other != '':
            text += u'=== Other ===\n' + other
    else:
        text += createSection(q, title, 'wdt:P31')
    text += u'[[Category:Wikidata:List of properties|' + title + ']]'
    page = pywikibot.Page(site, 'Wikidata:List of properties/' + title)
    try:
        page.put(text, summary='upd', minorEdit=False)
    except SpamblacklistError:
        pass


def createOverview():
    payload = {
        'query': """SELECT ?item (GROUP_CONCAT(?qfacet; separator=", ") as ?facets) (GROUP_CONCAT(?label; separator=", ") as ?labels){
                      ?item wdt:P279 wd:Q18616576
                      OPTIONAL { ?item wdt:P1269 ?facet . ?facet rdfs:label ?facetlabel . FILTER (LANG(?facetlabel) = 'en') }
                      BIND(IF(bound(?facet), substr(str(?facet), 32), substr(str(?item), 32)) AS ?qfacet)
                      ?item rdfs:label ?itemlabel . FILTER(LANG(?itemlabel) = 'en')
                      BIND(IF(bound(?facet), str(?facetlabel), str(?itemlabel)) AS ?label)
    }GROUP BY ?item ORDER BY fn:lower-case(?labels)""",
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    cat1st = {}
    text = u''
    i = 0
    for m in data['results']['bindings']:
        q = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        link = m['labels']['value'].split(',')[0]
        if ':' in link:
            link = m['labels']['value'].split(':')[1]
        if link in cat1st:
            link += ' (2)'
            if link in cat1st:
                link += ' (3)'
        cat1st[link] = q
        label = m['facets']['value'].replace('Q', '{{label|Q').replace(',', '}},') + '}}'
        if i % 5 == 0:
            text += u'|-\n'
        text += u"""|style="background-color:#eee; box-shadow: 0 0 .2em #999; border-radius: .2em; padding: 20px; width:20%; font-size:105%;"|\n'''[[Wikidata:List of properties/{0}|{1}]]'''\n""".format(link, label)
        i += 1

    page = pywikibot.Page(site, 'Wikidata:List of properties/cat overview')
    page.put(text, summary='upd', minorEdit=False)     
    
    return cat1st
    
def main():
    cat1st = createOverview()
    for cat in cat1st:
        createCatPage(cat, cat1st[cat])
    
if __name__ == "__main__":
    main()    
