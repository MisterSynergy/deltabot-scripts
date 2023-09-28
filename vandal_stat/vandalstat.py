# -*- coding: UTF-8 -*-

from os.path import expanduser
import mariadb
from datetime import date, timedelta
import pywikibot
import requests

site = pywikibot.Site('wikidata','wikidata')
repo = site.data_repository()

db = mariadb.connect(host="wikidatawiki.labsdb", database="wikidatawiki_p", default_file=f"{expanduser('~')}/replica.my.cnf")

r = requests.get('https://www.wikidata.org/w/index.php?title=Wikidata:WikiProject_Counter-Vandalism/plot1-csv&action=raw')
csv = r.text.split('\n')
newcsv = ''

oldest = date.today() - timedelta(31)
oldestformat = oldest.strftime('%Y%m%d')
oldestformat2 = oldest.strftime('%Y/%m/%d')
newest = date.today() - timedelta(1)
newestformat = newest.strftime('%Y%m%d')
newestformat2 = newest.strftime('%Y/%m/%d')


for line in csv:
    if 'unpatrolled edits' in line or 'IP' in line:
         continue
    if oldestformat2 in line:
         continue
    newcsv += line.strip()+'\n'

for dd in range(0,30):
    day = date.today() - timedelta(30-dd)
    dayformat = day.strftime('%Y%m%d')
    dayformat2 = day.strftime('%Y/%m/%d')

    cur = db.cursor(dictionary=True)
    cur.execute(
        'SELECT COUNT(*) as cnt FROM recentchanges WHERE rc_patrolled=0 AND rc_timestamp>%(dayformat_start)s AND rc_timestamp<=%(dayformat_end)s',
        {
            'dayformat_start' : f'{dayformat}000000',
            'dayformat_end' : f'{dayformat}235959',
        }
    )
    
    for row in cur.fetchall():
        newcsv += f'{dayformat2},{row.get("cnt", 0)},"unpatrolled edits"\n'

    cur.close()

cur = db.cursor(dictionary=True)
cur.execute(
    "SELECT COUNT(*) AS patrols FROM logging WHERE log_action='patrol' AND log_params LIKE '%\"6::auto\";i:0%' AND log_timestamp>%(newestformat_start)s AND log_timestamp<=%(newestformat_end)s",
    {
        'newestformat_start' : f'{newestformat}000000',
        'newestformat_end' : f'{newestformat}235959',
    }
)
for row in cur.fetchall():
    newcsv += f'{newestformat2},{row.get("patrols", 0)},"patrol actions"\n' 

cur.close()
db.close()

page = pywikibot.Page(site, 'Wikidata:WikiProject_Counter-Vandalism/plot1-csv')
page.put(newcsv, summary='upd', minorEdit=False)

