# -*- coding: utf-8  -*-
import requests
import json
import pywikibot
import datetime
from datetime import datetime
import time

site = pywikibot.Site('wikidata','wikidata')
repo = site.data_repository()


header = '== Implausbible Age ==\n\nList of all person who do not have an age between 0 and 130. Update: <onlyinclude>{0}</onlyinclude>\n\n\
{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"\n|- style="white-space:nowrap;"\n! Item !! Birth !! Death !! Age\n'
footer = '|}'
table_row = '|-\n| {{{{Q|{0}}}}} || {1}-{2:02d}-{3:02d} || {4}-{5:02d}-{6:02d} || {7}\n'

def calcAge(year1,month1,day1,year2,month2,day2):
    if month2<month1 or (month1==month2 and day2<day1):
        return year2-year1-1
    else:
        return year2-year1

def addRow(q):
    try:
        item = pywikibot.ItemPage(repo,q)
        dict = item.get()
        for m in dict['claims']['P569']:
            if m.getTarget().precision >= 9 and m.rank != 'deprecated':
                for n in dict['claims']['P570']:
                    if n.getTarget().precision >= 9 and n.rank != 'deprecated':
                        age = calcAge(m.getTarget().year,m.getTarget().month,m.getTarget().day,n.getTarget().year,n.getTarget().month,n.getTarget().day)
                        if age < 0 or age > 130:
                            return table_row.format(q, m.getTarget().year, m.getTarget().month, m.getTarget().day, n.getTarget().year, n.getTarget().month, n.getTarget().day, age)
        return ''
    except:
        return ''

def makeReport():
    text = ''
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    #check if death date is 130 bigger than birth date
    query = 'SELECT DISTINCT ?entity WHERE {?entity wdt:P31 wd:Q5; wdt:P569 ?dob; wdt:P570 ?dod . FILTER (year(?dod) - year(?dob) > 130) } ORDER BY ?entity' #including precision times out
    payload = {
        'query': query,
        'format': 'json'
    }
    r = requests.get(url, params=payload)
    data = r.json()
    for result in data['results']['bindings']:
        q = result['entity']['value'][31:]
        text += addRow(q)
    #check if birth date is smaller than death date
    query = 'SELECT DISTINCT ?entity WHERE {?entity wdt:P31 wd:Q5; wdt:P569 ?dob; wdt:P570 ?dod . FILTER (year(?dod) < year(?dob)) } ORDER BY ?entity' #including precision times out
    payload = {
        'query': query,
        'format': 'json'
    }
    r = requests.get(url, params=payload)
    data = r.json()
    for result in data['results']['bindings']:
        q = result['entity']['value'][31:]
        text += addRow(q)
    return text

def main():
    page = pywikibot.Page(site,'User:Pasleim/Implausible/age')
    report = makeReport()
    text = header.format(time.strftime("%H:%M, %d %B %Y (%Z)")) + report + footer
    page.put(text, summary='upd', minorEdit=False)

if __name__ == "__main__":
    main()
