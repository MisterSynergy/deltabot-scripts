#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import time
import pywikibot
import sys
import re
import requests

site = pywikibot.Site('wikidata','wikidata')
whitelist = []
disam = []
names = []

#database queries
def getItems(wiki1, wiki2, cat1, cat2):
    cnx1 = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", db="wikidatawiki_p", read_default_file="replica.my.cnf", charset='utf8')
    cur = cnx1.cursor()
    cur.execute('SELECT a.ips_item_id, b.ips_item_id, a.ips_site_page, b.ips_site_page FROM (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki1+'") AND ips_site_id = "'+wiki2+'")a INNER JOIN (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki2+'") AND ips_site_id = "'+wiki1+'")b ON a.ips_site_page = b.ips_site_page')
    for row in cur.fetchall():
        yield row
    if cat1:
        cat1 = cat1.encode('utf-8')
        cur.execute('SELECT a.ips_item_id, b.ips_item_id, a.ips_site_page, b.ips_site_page FROM (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki1+'") AND ips_site_id = "'+wiki2+'")a INNER JOIN (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki2+'") AND ips_site_id = "'+wiki1+'")b ON CONCAT("'+cat1.decode('utf-8')+'",":",a.ips_site_page) = b.ips_site_page')
        for row in cur.fetchall():
            yield row
    if cat2:
        cat2 = cat2.encode('utf-8')
        cur.execute('SELECT a.ips_item_id, b.ips_item_id, a.ips_site_page, b.ips_site_page FROM (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki1+'") AND ips_site_id = "'+wiki2+'")a INNER JOIN (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki2+'") AND ips_site_id = "'+wiki1+'")b ON a.ips_site_page = CONCAT("'+cat2.decode('utf-8')+'",":",b.ips_site_page)')
        for row in cur.fetchall():
            yield row
    if cat1 and cat2:
        cur.execute('SELECT a.ips_item_id, b.ips_item_id, a.ips_site_page, b.ips_site_page FROM (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki1+'") AND ips_site_id = "'+wiki2+'")a INNER JOIN (SELECT ips_item_id, ips_site_page FROM wb_items_per_site WHERE ips_item_id NOT IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = "'+wiki2+'") AND ips_site_id = "'+wiki1+'")b ON CONCAT("'+cat1.decode('utf-8')+'",":",a.ips_site_page) = CONCAT("'+cat2.decode('utf-8')+'",":",b.ips_site_page)')
        for row in cur.fetchall():
            yield row
    cur.close()
    cnx1.close()

def updateList(id, wiki1, wiki2, wiki1s, wiki2s, cat1, cat2):
    # because this script can run in parallel, check again if the selected list is not already updating 
    cnx4 = MySQLdb.connect(host="tools-db", db="s51591__main", read_default_file="replica.my.cnf",charset='utf8')
    cur4 = cnx4.cursor()
    cur4.execute('SELECT update_running FROM merge_status WHERE id = ' + str(id))
    for row in cur4.fetchall():
        if row[0] != None:
            print(row[0])
            print(str(row[0]))
            print('update is meanwhile running')
            return 0
    # if it is not updating, set status to updating
    cur4.execute('UPDATE merge_status SET update_running = Now() WHERE id = ' + str(id))
    cur4.close()
    cnx4.commit()
    cnx4.close()
    
    url = 'User:Pasleim/projectmerge/'+wiki1+'-'+wiki2
    page = pywikibot.Page(site, url)    
    gen = getItems(wiki1, wiki2, cat1, cat2)
    pretext = ''
    accepted = 0
    excluded = 0
    for row in gen:
        if (row[0] not in disam and row[1] in disam) or (row[0] in disam and row[1] not in disam):
            continue
        if (row[0] in names) or (row[1] in names):
            continue
        if [row[0],row[1]] in whitelist or [row[1],row[0]] in whitelist:
            excluded+=1
        else:
            accepted+=1
            pretext += '#[[Q'+str(row[0])+']] ([[:'+wiki2s+':'+row[2].decode('utf-8')+']]) and '
            pretext += '[[Q'+str(row[1])+']] ([[:'+wiki1s+':'+row[3].decode('utf-8')+']])\n'
    #write text
    text = '{{User:Pasleim/projectmerge/header\n'
    text += '|wiki1='+wiki1+'\n'
    text += '|wiki2='+wiki2+'\n'
    text += '|candidates='+str(excluded+accepted)+'\n'
    text += '|excluded='+str(excluded)+'\n'
    text += '|remaining='+str(accepted)+'\n'
    text += '|update='+time.strftime("%Y-%m-%d %H:%M (%Z)")+'\n'
    text += '}}\n\n'    
    
    
    if (accepted) != 0:
        text += '== Merge candidates ==\n'+pretext
    
    #write to Wikidata
    f1 = open('logs/merge-project-log.dat','a');
    #try:
    #no new report is created if page does not exist and report is empty
    if accepted > 0 or page.exists():
        page.put(text, summary='upd', minorEdit=False)
    cnx5 = MySQLdb.connect(host="tools-db", db="s51591__main", read_default_file="replica.my.cnf")
    cur5 = cnx5.cursor()
    cur5.execute('UPDATE merge_status SET last_update = "'+time.strftime('%Y-%m-%d %H:%M:%S')+'", candidates="'+str(accepted)+'", update_running="0000-00-00 00:00:00" WHERE id="' + str(id) + '"')
    cur5.close()
    cnx5.commit()
    cnx5.close()
    f1.write(time.strftime("%Y-%m-%d %H:%M (%Z)")+'\tupdate '+wiki1+' '+wiki2+'\n')
    #except:
    #    f1.write(time.strftime("%Y-%m-%d %H:%M (%Z)")+'\tsaving problems '+wiki1+' '+wiki2+'\n')
    f1.close()


def main():
    #create whitelist
    
    # from Do_not_merge
    r = requests.get('https://www.wikidata.org/w/api.php?action=query&list=allpages&apprefix=Do%20not%20merge/&apnamespace=4&aplimit=500&format=json')
    data = r.json()
    for p in data['query']['allpages']:
        page = pywikibot.Page(site, p['title'])
        if page.isRedirectPage():
            continue
        text = page.get()
        res = re.findall(r'Q(\d+)(.*)Q(\d+)', text)
        for m in res:
            whitelist.append([int(m[0]), int(m[2])])
            
    # from links based on SPARQL
    properties = ['P1889', 'P629', 'P747', 'P144', 'P4969']
    for p in properties:
        payload = {
            'query': 'SELECT ?item ?item2 WHERE{ ?item wdt:'+p+' ?item2. minus { ?item rdf:type wikibase:Property } minus { ?item rdf:type ontolex:LexicalEntry } }',
            'format': 'json'
        }
        r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql', params=payload)
        try:
            data = r.json()
        except:
            return 0
        for m in data['results']['bindings']:
            try:
                whitelist.append([int(m['item']['value'].replace('http://www.wikidata.org/entity/Q', '')), int(m['item2']['value'].replace('http://www.wikidata.org/entity/Q', ''))])
            except:
                pass

    #load all names
    payload = {
        'query': 'SELECT ?item WHERE { ?item wdt:P31/wdt:P279* wd:Q82799 }',
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    for m in data['results']['bindings']:
        try:
            names.append(int(m['item']['value'].replace('http://www.wikidata.org/entity/Q', '')))
        except:
            pass

    #load all disam-items
    payload = {
        'query': 'SELECT ?item WHERE{ ?item wdt:P31/wdt:P279* wd:Q4167410 }',
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    for m in data['results']['bindings']:
        if 'http://www.wikidata.org/entity/Q' in m['item']['value']:
            disam.append(int(m['item']['value'].replace('http://www.wikidata.org/entity/Q', '')))
    #------
    # handle update which are running for more than 1 day like they are not running.
    cnx2 = MySQLdb.connect(host="tools-db", db="s51591__main", read_default_file="replica.my.cnf", charset='utf8')
    cur2 = cnx2.cursor()
    cur2.execute('UPDATE merge_status SET update_running = "0000-00-00 00:00:00" WHERE TIMESTAMPDIFF(DAY,update_running,NOW()) > 1')
    cnx2.commit() 

    # select which lists need an update
    if sys.argv[1] == 'all':
        cur2.execute('SELECT id, wiki1, wiki2, cat1, cat2 FROM merge_status WHERE TIMESTAMPDIFF(DAY,last_update,NOW()) > 6 AND update_running = "0000-00-00 00:00:00" LIMIT 150')
    elif sys.argv[1] == 'upd':
        cur2.execute('SELECT id, wiki1, wiki2, cat1, cat2 FROM merge_status WHERE update_requested > last_update AND update_running = "0000-00-00 00:00:00"')
    else:
        return 0
   
    for row in cur2.fetchall():
        wiki1 = row[1]
        wiki2 = row[2]
        print(wiki1, wiki2)
        wiki1s = False
        wiki2s = False
        if wiki1[-4:] == 'wiki':
            wiki1s = wiki1[:-4]
        elif wiki1[-9:] == 'wikiquote':
            wiki1s = 'q:'+wiki1[:-9]
        elif wiki1[-10:] == 'wikisource':
            wiki1s = 's:'+wiki1[:-10]
        elif wiki1[-10:] == 'wikivoyage':
            wiki1s = 'voy:'+wiki1[:-10]
        elif wiki1[-8:] == 'wikinews':
            wiki1s = 'n:'+wiki1[:-8]
        elif wiki1[-9:] == 'wikibooks':
            wiki1s = 'b:'+wiki1[:-9]
        elif wiki1[-11:] == 'wikiversity':
            wiki1s = 'v:'+wiki1[:-11]
        elif wiki1[-10:] == 'wiktionary':
            wiki1s = 'wikt:'+wiki1[:-10]

        if wiki2[-4:] == 'wiki':
            wiki2s = wiki2[:-4]
        elif wiki2[-9:] == 'wikiquote':
            wiki2s = 'q:'+wiki2[:-9]
        elif wiki2[-10:] == 'wikisource':
            wiki2s = 's:'+wiki2[:-10]
        elif wiki2[-10:] == 'wikivoyage':
            wiki2s = 'voy:'+wiki2[:-10]
        elif wiki2[-8:] == 'wikinews':
            wiki2s = 'n:'+wiki2[:-8]
        elif wiki2[-9:] == 'wikibooks':
            wiki2s = 'b:'+wiki2[:-9]
        elif wiki2[-11:] == 'wikiversity':
            wiki2s = 'v:'+wiki2[:-11]
        elif wiki2[-10:] == 'wiktionary':
            wiki2s = 'wikt:'+wiki2[:-10]
        print(wiki1s, wiki2s)
        if wiki1s and wiki2s:
            wiki1s = wiki1s.replace('_', '-')
            wiki2s = wiki2s.replace('_', '-')
            #try:
            if True:
                updateList(row[0], wiki1, wiki2, wiki1s, wiki2s, row[3], row[4])
            '''except:
                print('error updateList')
                f1 = open('logs/merge-project-log.dat','a');
                f1.write(time.strftime("%Y-%m-%d %H:%M (%Z)")+'\terror '+wiki1+' '+wiki2+'\n')
                f1.close()'''

if __name__ == "__main__":
    main()
