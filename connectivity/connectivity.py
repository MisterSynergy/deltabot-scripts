#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import time
import pywikibot
db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                     db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()

text = ''


def getData(project):
    global text
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    cur = db.cursor()
    cur.execute("SELECT ga, count(*) gap  FROM (SELECT COUNT(ips_item_id) AS ga, ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id='" +
                project+"') GROUP BY ips_item_id) AS subquery GROUP BY ga")
    collec = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    total = 0
    avg = 0
    for row in cur.fetchall():
        if row[0] == 1:
            collec[0] += row[1]
        elif row[0] == 2:
            collec[1] += row[1]
        elif row[0] <= 6:
            collec[2] += row[1]
        elif row[0] <= 11:
            collec[3] += row[1]
        else:
            collec[4] += row[1]
        total += row[1]
        avg += row[1]*(row[0]-1)
    if total >= 100:
        total = float(total)
        avg /= total
        text += '\n| '+project + ' || ' + \
            '{:,}'.format(int(total))+' || '+'{:4.1f}'.format(avg)
        for i in range(0, 5):
            text += ' || {:4.1f}'.format(collec[i]/total*100)+'%'
            db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                                 db="wikidatawiki_p", read_default_file="replica.my.cnf")
            cur = db.cursor()
        cur.execute("SELECT count(*) as count, ips_site_id FROM wb_items_per_site WHERE ips_item_id IN (SELECT ips_item_id FROM wb_items_per_site WHERE ips_site_id = '" +
                    project+"') AND ips_site_id <> '"+project+"' GROUP BY ips_site_id ORDER BY count DESC LIMIT 0,3")
        for row in cur.fetchall():
            text += ' || {} || {:,}'.format(row[1].decode(), row[0])
        text += '\n|-'


def main():
    global text
    header = '{| class="wikitable sortable"\n|-\n! colspan=3 |\n! colspan=5 | Items with sitelinks to # other projects\n! colspan=6 | Top 3 linked projects\n|-\n! Project \n! data-sort-type="number" | Total Items\n! data-sort-type="number" | Avg # of sitelinks\n! data-sort-type="number" |# 0\n! data-sort-type="number" |# 1\n! data-sort-type="number" |# 2-5\n! data-sort-type="number" |# 6-10\n! data-sort-type="number" |# >10\n! 1<sup>st</sup> \n! data-sort-type="number" | links\n! 2<sup>nd</sup> \n! data-sort-type="number" | links\n! 3<sup>rd</sup> \n! data-sort-type="number" | links\n|-'
    text += 'Update: <onlyinclude>' + \
        time.strftime("%Y-%m-%d %H:%M (%Z)")+'</onlyinclude>.\n\n'
    text += '== Wikipedia ==\n'+header
    db = MySQLdb.connect(host="wikidatawiki.labsdb",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    cur = db.cursor()
    cur.execute("SELECT DISTINCT ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wiki' AND ips_site_id <> 'commonswiki' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row[0].decode())
    text += '\n|}\n'

    text += '== Wikivoyage ==\n'+header
    db = MySQLdb.connect(host="wikidatawiki.labsdb",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    cur = db.cursor()
    cur.execute(
        "SELECT DISTINCT ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikivoyage' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row[0].decode())
    text += '\n|}\n'

    text += '== Wikisource ==\n'+header
    db = MySQLdb.connect(host="wikidatawiki.labsdb",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    cur = db.cursor()
    cur.execute(
        "SELECT DISTINCT ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikisource' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row[0].decode())
    text += '\n|}\n'

    text += '== Wikiquote ==\n'+header
    db = MySQLdb.connect(host="wikidatawiki.labsdb",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    cur = db.cursor()
    cur.execute(
        "SELECT DISTINCT ips_site_id FROM wb_items_per_site WHERE ips_site_id LIKE '%wikiquote' ORDER BY ips_site_id")
    for row in cur.fetchall():
        getData(row[0].decode())
    text += '\n|}\n'
    text += '\n[[Category:Wikidata statistics]]'

    site = pywikibot.Site('wikidata', 'wikidata')
    page = pywikibot.Page(site, 'User:Pasleim/Connectivity')
    page.put(text, summary='upd', minorEdit=False)


if __name__ == "__main__":
    main()
