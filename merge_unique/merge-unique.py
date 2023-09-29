#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

#providing a list with unique violations, the script looks for merge candidates. Preferable, the list should only contains items from the same namespace

import MySQLdb
import time
import pywikibot
import re

site = pywikibot.Site('wikidata','wikidata')
db = MySQLdb.connect(host='wikidatawiki.analytics.db.svc.eqiad.wmflabs', db='wikidatawiki_p', read_default_file='replica.my.cnf')
cur = db.cursor()
whitelist = []

props = ['P301', 'P94', 'P41', 'P646', 'P494', 'P229', 'P225', 'P910', 'P685', 'P442', 'P1566']

def getItems(p):
    page = pywikibot.Page(site,'Wikidata:Database_reports/Constraint violations/'+p)
    text = page.get()
    res = re.search(r'== "Unique value" violations ==([^=]+)', text)
    if res:
        lines = res.group(1).split('\n')
        for line in lines:
            line = line.strip()
            if ': [[Q' in line:
                line = line.split(': ')    
                elements = line[1].split(', ')
                for i in range(0,len(elements)-1):
                    for j in range(i+1,len(elements)):
                        cur.execute('SELECT a.ips_site_id FROM wb_items_per_site a INNER JOIN wb_items_per_site b ON a.ips_site_id = b.ips_site_id WHERE a.ips_item_id = "'+elements[i][3:-2]+'" AND b.ips_item_id = "'+elements[j][3:-2]+'"')
                        if cur.rowcount == 0:
                            yield (elements[i][3:-2],elements[j][3:-2],line[0])

def updateList(p):
    gen = getItems(p)
    pretext = ''
    accepted = 0
    excluded = 0
    for row in gen:
        if [row[0],row[1]] in whitelist or [row[1],row[0]] in whitelist:
            excluded+=1
        else:
            accepted+=1
            if accepted < 5000:
                pretext += row[2]+': {{Q|'+str(row[0])+'}}, {{Q|'+str(row[1])+'}}\n'

    #write text
    text = u'Merge candidates based on same {{P|'+p+'}} value.\n\n'
    text += u'Found '+str(excluded+accepted)+' merge candiates, excluding '+str(excluded)+' candidates from the [[Wikidata:Do not merge|whitelist]] leads to '+str(accepted)+' remaining candidates.\n\n'
    if (accepted) != 0:
        text += u'== Merge candidates ==\n' + pretext
    if accepted > 5000:
        skipped = accepted-5000
        text += '\nSkipping ' + str(skipped) + 'records\n'
    #write to wikidata
    page = pywikibot.Page(site, 'User:Pasleim/uniquemerge/'+p)
    page.put(text, summary='upd', minorEdit=False)

def main():
    #create whitelist
    page = pywikibot.Page(site,'Wikidata:Do not merge')
    text = page.get()
    res = re.findall(r'Q(\d+)(.*)Q(\d+)', text)
    for m in res:
        whitelist.append([int(m[0]), int(m[2])])

    for p in props:
        try:
            updateList(p)
        except:
            pass

if __name__ == '__main__':
    main()

