#!/usr/bin/python
# -*- coding: UTF-8 -*-

import MySQLdb
import pywikibot
import time, datetime
import requests
import json
import sys

today = datetime.datetime.now()

cats = [
    {'wiki' : 'en', 'prefix' : '', 'suffix' : '_deaths'},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_janvier_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_février_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_mars_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_avril_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_mai_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_juin_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_juillet_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_août_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_septembre_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_octobre_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_novembre_', 'suffix' : ''},
    {'wiki' : 'fr', 'prefix' : 'Décès_en_décembre_', 'suffix' : ''},    
    {'wiki' : 'de', 'prefix' : 'Gestorben_', 'suffix': ''},
    {'wiki' : 'ru', 'prefix' : 'Умершие_в_', 'suffix': '_году'},
    {'wiki' : 'simple', 'prefix' : '', 'suffix': '_deaths'},
    {'wiki' : 'pl', 'prefix' : 'Zmarli_w_', 'suffix': ''},
    {'wiki' : 'es', 'prefix' : 'Fallecidos_en_', 'suffix': ''},
    {'wiki' : 'it', 'prefix' : 'Morti_nel_', 'suffix': ''},
    {'wiki' : 'ja', 'prefix' : '', 'suffix': '年没'},
    {'wiki' : 'fi', 'prefix' : 'Vuonna_', 'suffix': '_kuolleet'},
    {'wiki' : 'tr', 'prefix' : '', 'suffix': '_yılında_ölenler'},
    {'wiki' : 'sv', 'prefix' : 'Avlidna_', 'suffix': ''},
    {'wiki' : 'pt', 'prefix' : 'Mortos_em_', 'suffix': ''},
    {'wiki' : 'zh', 'prefix' : '', 'suffix': '年逝世'},
    {'wiki' : 'uk', 'prefix' : 'Померли_', 'suffix': ''},
    {'wiki' : 'cs', 'prefix' : 'Úmrtí_', 'suffix': ''},
    {'wiki' : 'hu', 'prefix' : '', 'suffix': '-ban_elhunyt_személyek'},
    {'wiki' : 'hu', 'prefix' : '', 'suffix': '-ben_elhunyt_személyek'},
    {'wiki' : 'ar', 'prefix' : 'وفيات_', 'suffix': ''},
    {'wiki' : 'no', 'prefix' : 'Dødsfall_i_', 'suffix': ''},
    {'wiki' : 'la', 'prefix' : 'Mortui_', 'suffix': ''},    
    {'wiki' : 'et', 'prefix' : 'Surnud_', 'suffix': ''},
    {'wiki' : 'da', 'prefix' : 'Døde_i_', 'suffix': ''},
    {'wiki' : 'ko', 'prefix' : '', 'suffix': '년_죽음'},
    {'wiki' : 'id', 'prefix' : 'Kematian_', 'suffix': ''},
    {'wiki' : 'eo', 'prefix' : 'Mortintoj_en_', 'suffix': ''},
    {'wiki' : 'bg', 'prefix' : 'Починали_през_', 'suffix': '_година'},
    {'wiki' : 'ro', 'prefix' : 'Decese_în_', 'suffix': ''},
    {'wiki' : 'eu', 'prefix' : '', 'suffix': 'eko_heriotzak'},
    {'wiki' : 'eu', 'prefix' : '', 'suffix': 'ko_heriotzak'},
    {'wiki' : 'sk', 'prefix' : 'Úmrtia_v_', 'suffix': ''},
    {'wiki' : 'sl', 'prefix' : 'Umrli_leta_', 'suffix': ''},
    {'wiki' : 'sco', 'prefix' : '', 'suffix': '_daiths'},
    {'wiki' : 'el', 'prefix' : 'Θάνατοι_το_', 'suffix': ''},    
    {'wiki' : 'az', 'prefix' : '', 'suffix': '-ci_ildə_vəfat_edənlər'},
    {'wiki' : 'az', 'prefix' : '', 'suffix': '-cı_ildə_vəfat_edənlər'},
    {'wiki' : 'az', 'prefix' : '', 'suffix': '-cü_ildə_vəfat_edənlər'},
    {'wiki' : 'az', 'prefix' : '', 'suffix': '-cu_ildə_vəfat_edənlər'},
    {'wiki' : 'lb', 'prefix' : 'Gestuerwen_', 'suffix': ''},
    {'wiki' : 'gl', 'prefix' : 'Finados_en_', 'suffix': ''},    
    {'wiki' : 'cy', 'prefix' : 'Marwolaethau_', 'suffix': ''},
    {'wiki' : 'ta', 'prefix' : '', 'suffix': '_இறப்புகள்'},
    {'wiki' : 'sr', 'prefix' : 'Умрли_', 'suffix': ''},    
    {'wiki' : 'vi', 'prefix' : 'Mất_', 'suffix': ''},
    {'wiki' : 'nn', 'prefix' : 'Døde_i_', 'suffix': ''},
    {'wiki' : 'hy', 'prefix' : '', 'suffix': '_մահեր'},    
    {'wiki' : 'sh', 'prefix' : 'Umrli_', 'suffix': '.'},
    {'wiki' : 'mk', 'prefix' : 'Починати_во_', 'suffix': '_година'},
    {'wiki' : 'kk', 'prefix' : '', 'suffix': '_жылы_қайтыс_болғандар'},
    {'wiki' : 'ca', 'prefix' : 'Morts_el_', 'suffix': ''},
    {'wiki' : 'ms', 'prefix' : 'Kematian_', 'suffix': ''},
    {'wiki' : 'ur', 'prefix' : 'ء_کی_وفیات', 'suffix': ''},
    {'wiki' : 'be', 'prefix' : 'Памерлі_ў_', 'suffix': '_годзе'},
    {'wiki' : 'zh_min_nan', 'prefix' : '', 'suffix': '_nî_kòe-sin'},
    {'wiki' : 'ka', 'prefix' : 'გარდაცვლილი_', 'suffix': ''}
]    

site = pywikibot.Site('wikidata','wikidata')

header = 'Persons deceased in {0} according to Wikipedia, but without {{{{P|570}}}} at Wikidata. Data as of {1}.\n\n{{{{Wikidata:Database reports/Deaths at Wikipedia/header-year}}}}<onlyinclude>\n'
footer = '</onlyinclude></table>\n\n[[Category:Database reports deaths by year|{0}]]__NOINDEX__' 
table_row = '{{{{tr peoplelist 4|{0}|{1}|{2}|{3}|{4}}}}}\n'
stat = '{{{{DR rd numbers-1|year={0}|items={1}|latest={2}|en={3}|nonroman={4}|cyr={5}|ar={6}|ja={7}|zh={8}|24h={9}|48h={10}|7d={11}|30d={12}|365dp={13}}}}}'
comment_template = 'Bot: Updating Database report: {0} items; latest: {1}; en: {2}; nonroman: {3}; ar: {4}, ja: {5}, zh: {6}, cyr: {7}; AGING 24h: {8}, 48h: {9}, 7d: {10}, 30d: {11},  365+d: {12}'
commentall_template = 'Bot: Updating Database report {0} years: {1} items; latest: {2}; en: {3}; nonroman: {4}; ar: {5}, ja: {6}, zh: {7}, cyr: {8}; AGING 24h: {9}, 48h: {10}, 7d: {11},  30d: {12},  365+d: {13}'
summary_row = '{{{{DR rd numbers-y|year={0}|items={1}|latest={2}|en={3}|nonroman={4}|cyr={5}|ar={6}|ja={7}|zh={8}|24h={9}|48h={10}|7d={11}|30d={12}|365dp={13}|earliest={14}}}}}\n'

def makeReport(yr):
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs", read_default_file="replica.my.cnf")
    thaiyear = str(int(yr)+543)

    query = 'SELECT SQL_NO_CACHE wp.pp_value, GROUP_CONCAT(wp.wiki) AS wikis, MIN(wp.cl_timestamp) FROM (' 
    query += '(SELECT pp_value, cl_timestamp, "commons" AS Wiki FROM commonswiki_p.categorylinks JOIN commonswiki_p.page_props ON pp_page=cl_from WHERE cl_to="'+yr+'_deaths" AND pp_propname="wikibase_item" AND cl_type="subcat" ) '
    query += 'UNION ALL (SELECT pp_value, cl_timestamp, "th" AS Wiki FROM thwiki_p.categorylinks JOIN thwiki_p.page_props ON pp_page=cl_from WHERE cl_to="บุคคลที่เสียชีวิตในปี_พ.ศ._'+thaiyear+'" AND pp_propname="wikibase_item" AND cl_type="page" ) '
    for m in cats:
        query += 'UNION ALL (SELECT pp_value, cl_timestamp, "'+m['wiki']+'" AS Wiki FROM '+m['wiki']+'wiki_p.categorylinks JOIN '+m['wiki']+'wiki_p.page_props ON pp_page=cl_from WHERE cl_to="'+m['prefix']+yr+m['suffix']+'" AND pp_propname="wikibase_item" AND cl_type="page" ) '
    query += ') AS wp '
    query += 'WHERE wp.pp_value NOT IN (SELECT page_title FROM wikidatawiki_p.page JOIN wikidatawiki_p.pagelinks ON page_id=pl_from WHERE pl_title = "P570" AND pl_namespace = 120) '
    query += 'AND NOT EXISTS (SELECT * FROM wikidatawiki_p.page WHERE page_is_redirect = 1 AND page_title = wp.pp_value) ' 
    query += 'GROUP BY wp.pp_value ORDER BY MIN(wp.cl_timestamp)'


    cursor = db.cursor()
    cursor.execute(query.encode('utf-8'))
    report = ''
    rowct = 0
    enwiki = 0
    zhwiki = 0
    arwiki = 0
    jawiki = 0
    days1 = 0
    days2 = 0
    days7 = 0
    days30 = 0
    days365p = 0
    nonromanwiki = 0
    nonroman = ['ja','zh','ar','ru','uk','fa','ko','hy','el','th','ta','mr','kk','mk','sr','be','bg','ur','zh_min_nan','ka']
    cyr = 0
    cyr_lang = ['ru', 'uk', 'sr', 'mk', 'kk', 'bg','be']
    latest = ''
    earliest = ''
    for q, wikis, ts in cursor:
        q = q.decode().upper()
        payload = {
            'action' : 'wbgetentities',
            'ids' : q,
            'props' : 'labels|claims',
            'format' : 'json'
        }
        r = requests.get('https://www.wikidata.org/w/api.php', params = payload)
        data = r.json()
        if 'claims' in data['entities'][q]:
            if 'P31' in data['entities'][q]['claims']:
                human = 0
                for m in data['entities'][q]['claims']['P31']:
                    if m['mainsnak']['datavalue']['value']['numeric-id'] == 5:
                        human = 1
                if human == 0:
                    continue
        label = q
        if 'labels' in data['entities'][q]:
            if 'en' in data['entities'][q]['labels']:
                label = data['entities'][q]['labels']['en']['value']
            elif wikis in data['entities'][q]['labels']:
                label = data['entities'][q]['labels'][wikis]['value']
        rowct += 1
        if rowct == 1:
            earliest = str(ts)
        if ("commons," in wikis) == True: 
            wikis= wikis.replace("commons,", "") + ",commons"
        if (",en" in wikis) == True: 
            wikis= "en," + wikis.replace(",en", "", 1)
        report += table_row.format(q, wikis, ts, label, rowct)
        if 'en' in wikis: enwiki += 1
        if 'ar' in wikis: arwiki += 1 
        if 'ja' in wikis: jawiki += 1
        if 'zh' in wikis: zhwiki += 1 
        if any(x in wikis for x in nonroman): nonromanwiki +=1
        if any(x in wikis for x in cyr_lang): cyr +=1
        if str(ts) > latest: latest = str(ts)
        if ts > (today-datetime.timedelta(days=1)): days1 +=1
        if ts > (today-datetime.timedelta(days=2)): days2 +=1
        if ts > (today-datetime.timedelta(days=7)): days7 +=1
        if ts > (today-datetime.timedelta(days=30)): days30 +=1
        if ts < (today-datetime.timedelta(days=365)): days365p +=1
        
    pagename = 'Wikidata:Database reports/Deaths at Wikipedia/' + str(yr)
    page = pywikibot.Page(site, pagename)      
    text = stat.format(yr, rowct, latest, enwiki, nonromanwiki, cyr, arwiki, jawiki, zhwiki, days1, days2, days7, days30, days365p)
    text += header.format(yr, time.strftime("%Y-%m-%d %H:%M (%Z)")) 
    text += report
    text += footer.format(yr)
    comment = comment_template.format(rowct, latest, enwiki, nonromanwiki, arwiki, jawiki, zhwiki, cyr, days1, days2, days7, days30, days365p)
    page.put(text, summary=comment, minorEdit=False)
    return text, rowct, enwiki, arwiki, jawiki, zhwiki, nonromanwiki, cyr, latest, days1, days2, days7, days30, days365p, earliest

def main():
    if sys.argv[1] != 'all':
        makeReport(sys.argv[1])
    else:
        allsummary = ''
        Arowct = Aenwiki = Aarwiki = Ajawiki = Azhwiki = Anonromanwiki = Acyr = Alatest = Adays1 = Adays2 = Adays7 = Adays30 = Adays365p = yrs = 0
        for yr in range(1941, today.year+1):
            yrs += 1

            try:
                report, rowct, enwiki, arwiki, jawiki, zhwiki, nonromanwiki, cyr, latest, days1, days2, days7, days30, days365p, earliest = makeReport(str(yr))
                Arowct, Aenwiki, Aarwiki, Ajawiki, Azhwiki, Anonromanwiki, Acyr, Adays1, Adays2, Adays7, Adays30, Adays365p  = Arowct+rowct, Aenwiki+enwiki, Aarwiki+arwiki, Ajawiki+jawiki, Azhwiki+zhwiki, Anonromanwiki+nonromanwiki, Acyr+cyr, Adays1+days1, Adays2+days2, Adays7+days7, Adays30+days30, Adays365p+days365p
                if latest > str(Alatest): Alatest = latest
                allsummary += summary_row.format(yr, rowct, latest, enwiki, nonromanwiki, cyr, arwiki, jawiki, zhwiki, days1, days2, days7, days30, days365p, earliest)
            except:
                print('error with year '+str(yr))

        page = pywikibot.Page(site, 'Wikidata:Database reports/Deaths at Wikipedia')
        text = '{{Wikidata:Database reports/Deaths at Wikipedia/header}}\n' + allsummary + '</table>\n\n[[Category:Database reports deaths by year| ]]'
        comment = commentall_template.format(yrs, Arowct, Alatest, Aenwiki, Anonromanwiki, Aarwiki, Ajawiki, Azhwiki, Acyr, Adays1, Adays2, Adays7, Adays30, Adays365p)
        page.put(text, summary=comment, minorEdit=False)
    
if __name__ == "__main__":
    main()
