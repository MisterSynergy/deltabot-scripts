# -*- coding: UTF-8 -*-
# licensed under MIT: http://opensource.org/licenses/MIT

import MySQLdb
import time
import pywikibot

db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                     db="wikidatawiki_p", read_default_file="replica.my.cnf")
cur = db.cursor()

cur.execute(
    "SELECT count(*) FROM page WHERE page_namespace = 0 ANd page_is_redirect=0")
blo = cur.fetchall()
total = blo[0][0]
cur.execute("SELECT count(*) FROM wb_items_per_site")
blo = cur.fetchall()
allLinks = blo[0][0]

pedia = 0
voyage = 0
source = 0
quote = 0
news = 0
books = 0
versity = 0
wiktionary = 0
other = 0

text = 'Update: <onlyinclude>' + \
    time.strftime("%Y-%m-%d %H:%M (%Z)")+'</onlyinclude>.\n\n'
text += 'Total items: '+('{:,}'.format(total))+'\n\n'
text += '== Number of sitelinks ==\n'

# number of sitelinks per project
text += '{|\n|- style="vertical-align:top;"\n|\n{| class="wikitable sortable" style="margin-right:50px;"\n|+ Sitelinks per project\n|-\n! Project\n! data-sort-type="number"|# of sitelinks\n'

cur.execute(
    "SELECT ips_site_id, count(*) FROM wb_items_per_site GROUP BY ips_site_id ORDER BY ips_site_id")

for row in cur.fetchall():
    sitetype = row[0].decode()
    if 'voyage' in sitetype:
        text += '|- style="background: Bisque"\n'
        voyage += row[1]
    elif 'source' in sitetype:
        text += '|- style="background: LightCyan"\n'
        source += row[1]
    elif 'commonswiki' == sitetype or 'wikidatawiki' == sitetype or 'specieswiki' == sitetype or 'metawiki' == sitetype or 'mediawikiwiki' == sitetype:
        text += '|- style="background: SkyBlue"\n'
        other += row[1]
    elif 'quote' in sitetype:
        text += '|- style="background: MistyRose"\n'
        quote += row[1]
    elif 'news' in sitetype:
        text += '|- style="background: PaleGreen"\n'
        news += row[1]
    elif 'books' in sitetype:
        text += '|- style="background: #E9DDAF"\n'
        books += row[1]
    elif 'wiktionary' in sitetype:
        text += '|- style="background: #CCF9CC"\n'
        wiktionary += row[1]
    elif 'versity' in sitetype:
        text += '|- style="background: #CFDBC5"\n'
        versity += row[1]

    else:
        text += '|-\n'
        pedia += row[1]
    text += '| '+sitetype+' || '+('{:,}'.format(row[1]))+'\n'

text += '|-\n! Total !! '+('{:,}'.format(allLinks)) + \
    ' ('+str(round(allLinks/(float)(total), 2))+' per Item)\n'
text += '|}\n|\n'

# summary
text += '{| class="wikitable sortable" style="margin-right:50px;"\n|+ Summary\n|-\n! Projects\n! data-sort-type="number"|# of sitelinks\n|-\n| wikipedia || '+('{:,}'.format(pedia))+'\n|- style="background: Bisque"\n| wikivoyage || '+('{:,}'.format(voyage))+'\n|- style="background: LightCyan"\n| wikisource || '+('{:,}'.format(source))+'\n|- style="background: MistyRose"\n| wikiquote || '+('{:,}'.format(
    quote))+'\n|- style="background: PaleGreen"\n| wikinews || '+('{:,}'.format(news))+'\n|- style="background: #E9DDAF"\n| wikibooks || '+('{:,}'.format(books))+'\n|- style="background: #CFDBC5"\n| wikiversity || '+('{:,}'.format(versity))+'\n|- style="background: #CCF9CC"\n| wiktionary || '+('{:,}'.format(wiktionary))+'\n|- style="background: SkyBlue"\n | other || '+('{:,}'.format(other))+'\n|}\n|\n'

# number of sitelinks per item
text += '{| class="wikitable sortable"\n|+ Sitelinks per item\n|-\n! data-sort-type="number"| sitelinks\n! data-sort-type="number" |# of items'

cur.execute(
    "SELECT pp_value, count(*) FROM page_props WHERE pp_propname = 'wb-sitelinks' GROUP BY pp_value")

collec = {}

for row in cur.fetchall():
    if int(row[0]) < 10:
        bin = int(row[0])
    elif int(row[0]) < 100:
        bin = int(row[0]/10)*10
    else:
        bin = int(row[0]/100)*100
    if bin in collec:
        collec[bin] += int(row[1])
    else:
        collec[bin] = int(row[1])

for m in sorted(collec):
    text += '\n|-\n| '+str(m)
    if m >= 10 and m < 100:
        text += '-'+str(m+9)
    if m >= 100:
        text += '-'+str(m+99)
    text += ' links || '+('{:,}'.format(collec[m]))

text += '\n|}\n|}\n'
text += '\n[[Category:Wikidata statistics|Sitelink statistics]]'

# write to wikidata
site = pywikibot.Site('wikidata', 'wikidata')
page = pywikibot.Page(site, 'User:Pasleim/Sitelink statistics')
page.put(text, summary='upd', minorEdit=False)
