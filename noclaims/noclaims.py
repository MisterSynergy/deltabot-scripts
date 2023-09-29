#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time
import requests

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

header = 'A list of items with a sitelink to {0} but without any statements. Data as of <onlyinclude>{1}</onlyinclude>.\n\n'
table_row = '* [[{0}]] - [[:{1}:{2}]]\n'

table_row_overview = '{{{{TR otherreport|{0}|{1}|{2}|{3}|{4}|{5}}}}}\n'
header_overview = '{{{{Wikidata:Database reports/without claims by site/header|{0}}}}}\n'
footer_overview = '{{Wikidata:Database reports/without claims by site/footer}} __NOINDEX__'
query2 = 'SELECT ips_site_id AS sit, COUNT(*) AS ct FROM wb_items_per_site GROUP BY ips_site_id ORDER BY ct DESC'
#query3 = 'SELECT ips_site_id AS sit, COUNT(*) AS ct FROM page_props, wb_items_per_site, page WHERE pp_sortkey = 0 AND pp_propname="wb-claims" AND pp_page = page_id AND CONCAT("Q", ips_item_id) = page_title AND page_namespace = 0 GROUP BY ips_site_id ORDER BY ct DESC'
query3 = 'SELECT COUNT(*) AS ct FROM page_props, wb_items_per_site, page WHERE pp_sortkey = 0 AND pp_propname="wb-claims" AND pp_page = page_id AND CONCAT("Q", ips_item_id) = page_title AND page_namespace = 0 AND ips_site_id = "{}"'


def wikisite(sit):
    if sit in ('commonswiki', 'specieswiki', 'metawiki'):
        group = 'wikimedia'
        sdomain = sit.split('wiki')[0]
    elif sit in ('wikidatawiki', 'mediawikiwiki'):
        sdomain = 'www'
        group = sit.split('wiki')[0]
    else:
        sdomain, group = sit.split('wik')
        sdomain = sdomain.replace('_', '-')
        if sdomain == 'nb':
            sdomain = 'no'
        group = 'wik'+group
        if group == 'wiki':
            group = 'wikipedia'
    return sdomain, group


def makeReport(s):
    payload = {
        'query': """SELECT ?item ?article WHERE {
                           ?article schema:about ?item ;
                                    schema:isPartOf <https://"""+s+""".wikipedia.org/> .
                           ?item wikibase:statements "0"^^xsd:integer.
                   } ORDER BY DESC(xsd:integer(SUBSTR(STR(?item),STRLEN("http://www.wikidata.org/entity/Q")+1))) LIMIT 1000""",
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    text = ''    
    for m in data['results']['bindings']:
        qid = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        article = m['article']['value'].split('/wiki/')[1]
        text += table_row.format(qid, s, article)  
    return text


def makeOverview():
    print('start overview')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")

    cursor2 = db.cursor()
    cursor2.execute(query2)
    idx = 0    
    maxvalue = 0
    text = ''
    print('query2 done')
    for sit, cntAll in cursor2:
        print(sit)
        idx += 1
        db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf")
        cursor = db.cursor()
        cursor.execute(query3.format(sit.decode('utf-8')))       
        for cntWithout in cursor:
            if cntWithout[0] > maxvalue:
                maxvalue = cntWithout[0]
            lang, group = wikisite(sit.decode('utf-8'))
            text += table_row_overview.format(sit, lang, group, cntWithout[0], idx, cntAll)                
    return text, idx, maxvalue


def main():
    for s in ['de', 'en', 'eo', 'et', 'fr', 'ja', 'nl', 'pt', 'ru', 'sv']:
        try:
            page = pywikibot.Page(site, 'Wikidata:Database reports/without claims by site/'+s+'wiki')
            report = makeReport(s)
            text = header.format(s, time.strftime("%Y-%m-%d %H:%M (%Z)")) + report
            summary = 'Bot: Updating database report'
            page.put(text, summary=summary, minorEdit=False)
        except:
            print('error '+s)
    '''page = pywikibot.Page(site, 'Wikidata:Database reports/without claims by site')
    report, idx, maxvalue = makeOverview()
    stat = '{{{{DR otherreport|max={}|reportlength={}}}}}\n'.format(maxvalue, idx)
    text = stat + header_overview.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + footer_overview
    summary = 'Bot: Updating database report: reportlength: {}; max: {}'.format(idx, maxvalue)
    page.put(text.decode('UTF-8'), summary=summary, minorEdit=False)
    '''

if __name__ == "__main__":
    main()
