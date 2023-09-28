#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import mariadb
from os.path import expanduser
import time
import pywikibot


text = ''


def getData(project):
    global text
    db = mariadb.connect(host="wikidatawiki.analytics.db.svc.wikimedia.cloud",
                         database="wikidatawiki_p", default_file=f"{expanduser('~')}/replica.my.cnf")
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT ga, COUNT(*) AS gap FROM (SELECT COUNT(ips_item_id) AS ga, ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id=%(project)s) GROUP BY ips_item_id) AS subquery GROUP BY ga",
        { 'project' : project },
    )
    collec = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    total = 0
    avg = 0
    for row in cur.fetchall():
        if row.get('ga') == 1:
            collec[0] += row.get('gap')
        elif row.get('ga') == 2:
            collec[1] += row.get('gap')
        elif row.get('ga') <= 6:
            collec[2] += row.get('gap')
        elif row.get('ga') <= 11:
            collec[3] += row.get('gap')
        else:
            collec[4] += row.get('gap')
        total += row.get('gap')
        avg += row.get('gap')*(row.get('ga')-1)
    cur.close()

    if total >= 100:
        total = float(total)
        avg /= total
        text += '\n| '+project + ' || ' + \
            '{:,}'.format(int(total))+' || '+'{:4.1f}'.format(avg)
        for i in range(0, 5):
            text += ' || {:4.1f}'.format(collec[i]/total*100)+'%'
        
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT count(*) AS count, CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = %(project)s) AND ips_site_id <> %(project)s GROUP BY ips_site_id ORDER BY count DESC LIMIT 0,3",
            { 'project' : project }
        )
        for row in cur.fetchall():
            text += ' || {} || {:,}'.format(row.get('ips_site_id', ''), row.get('count', 0))
        text += '\n|-'
        cur.close()

    db.close()


def main():
    global text
    header = '{| class="wikitable sortable"\n|-\n! colspan=3 |\n! colspan=5 | Items with sitelinks to # other projects\n! colspan=6 | Top 3 linked projects\n|-\n! Project \n! data-sort-type="number" | Total Items\n! data-sort-type="number" | Avg # of sitelinks\n! data-sort-type="number" |# 0\n! data-sort-type="number" |# 1\n! data-sort-type="number" |# 2-5\n! data-sort-type="number" |# 6-10\n! data-sort-type="number" |# >10\n! 1<sup>st</sup> \n! data-sort-type="number" | links\n! 2<sup>nd</sup> \n! data-sort-type="number" | links\n! 3<sup>rd</sup> \n! data-sort-type="number" | links\n|-'
    text += 'Update: <onlyinclude>' + \
        time.strftime("%Y-%m-%d %H:%M (%Z)")+'</onlyinclude>.\n\n'
    text += '== Wikipedia ==\n'+header
    db = mariadb.connect(host="wikidatawiki.analytics.db.svc.wikimedia.cloud",
                         database="wikidatawiki_p", default_file=f"{expanduser('~')}/replica.my.cnf")
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wiki' AND ips_site_id <> 'commonswiki' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row.get('ips_site_id'))
    text += '\n|}\n'
    cur.close()

    text += '== Wikivoyage ==\n'+header
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikivoyage' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row.get('ips_site_id'))
    text += '\n|}\n'
    cur.close()

    text += '== Wikisource ==\n'+header
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikisource' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row.get('ips_site_id'))
    text += '\n|}\n'
    cur.close()

    text += '== Wikiquote ==\n'+header
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT DISTINCT CONVERT(ips_site_id USING utf8) AS ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikiquote' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row.get('ips_site_id'))
    text += '\n|}\n'
    cur.close()
    db.close()

    text += '\n[[Category:Wikidata statistics]]'

    site = pywikibot.Site('wikidata', 'wikidata')
    page = pywikibot.Page(site, 'User:Pasleim/Connectivity')
    page.put(text, summary='upd', minorEdit=False)


if __name__ == "__main__":
    main()
