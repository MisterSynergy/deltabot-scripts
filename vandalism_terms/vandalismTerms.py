#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
import re

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
page = pywikibot.Page(site,'User:Pasleim/Vandalism')

text = u'The following unpatrolled items might be vandalised. Please either revert the edits or mark them as patrolled.\n\n'
text += '{| class="wikitable sortable plainlinks"\n! Item !! Term !! Action !! Language !! Filter !! User !! Timestamp\n'

latin = ['af','ak','an','ang','ast','ay','az','bar','bcl','bi','bm','br','bs','ca','cbk-zam','ceb','ch','chm','cho','chy','co','crh-latn','cs','csb','cy','da','de','diq','dsb','ee','eml','en','eo','es','et','eu','ff','fi','fit','fj','fo','fr','frp','frr','fur','fy','ga','gd','gl','gn','gsw','gv','ha','haw','ho','hr','hsb','ht','hu','hz','id','ie','ig','ik','ilo','io','is','it','jbo','jv','kab','kg','ki','kj','kl','kr','ksh','ku','kw','la','lad','lb','lg','li','lij','lmo','ln','lt','lv','map-bms','mg','mh','mi','min','ms','mt','mus','mwl','na','nah','nan','nap','nb','nds','nds-nl','ng','nl','nn','nov','nrm','nv','ny','oc','om','pag','pam','pap','pcd','pdc','pih','pl','pms','pt','qu','rm','rn','ro','roa-tara','rup','rw','sc','scn','sco','se','sg','sgs','sk','sl','sm','sn','so','sq','sr-el','ss','st','stq','su','sv','sw','szl','tet','tk','tl','tn','to','tpi','tr','ts','tum','tw','ty','uz','ve','vec','vi','vls','vo','vro','wa','war','wo','xh','yo','za','zea','zu']

def filter(term,termtype,lang):
    if re.search(u'(\!\!|\?\?|\.\.|,,|\<|\>)',term):
        return 'punctuation'
    if re.search(u'[A-Z]{5,}',term):
        return 'upper case'
    if re.search(u'[0-9]{6,}',term):
        return 'long number'
    if re.search(u'(http|www|\:\/\/)',term.lower()):
        return 'URL'
    if re.search(u'(language\-|description|label|alias|jpg|svg|^test$)',term.lower()):
        return 'suspicious words'
    if re.search(u'^([b-df-hj-np-tv-xz]{2,6}|[aeiouy][b-df-hj-np-tv-xz][bcdfghjkmnpqstvwxz]{2,5}[aeiouy]?|[b-df-hj-np-tv-xz][bcdfghjkmnpqstvwxz]{3,5}[aeiouy])$',term): #filter 46
        return 'nonsense'
    if lang in latin:
        if len(term) < 4 and termtype=='description':
            return 'short description'
        if re.search(u'[\u4e00-\u9fff]+|[\u0400-\u0500]+',term): #chinese and cyrillic characters
            return 'wrong script'
    if re.search(u'^([ei]n )?(a(frikaa?ns|lbanian?|lemanha|ng(lais|ol)|ra?b(e?|[ei]c|ian?|isc?h)|rmenian?|ssamese|azeri|z[eə]rba(ijani?|ycan(ca)?|yjan)|нглийский)|b(ahasa( (indonesia|jawa|malaysia|melayu))?|angla|as(k|qu)e|[aeo]ng[ao]?li|elarusian?|okmål|osanski|ra[sz]il(ian?)?|ritish( kannada)?|ulgarian?)|c(ebuano|hina|hinese( simplified)?|zech|roat([eo]|ian?)|atal[aà]n?|рпски|antonese)|[cč](esky|e[sš]tina)|d(an(isc?h|sk)|e?uts?ch)|e(esti|ll[hi]nika|ng(els|le(ski|za)|lisc?h)|spa(g?[nñ]h?i?ol|nisc?h)|speranto|stonian|usk[ae]ra)|f(ilipino|innish|ran[cç](ais|e|ez[ao])|ren[cs]h|arsi|rancese)|g(al(ego|ician)|uja?rati|ree(ce|k)|eorgian|erman[ay]?|ilaki)|h(ayeren|ebrew|indi|rvatski|ungar(y|ian))|i(celandic|ndian?|ndonesian?|ngl[eê]se?|ngilizce|tali(ano?|en(isch)?))|ja(pan(ese)?|vanese)|k(a(nn?ada|zakh)|hmer|o(rean?|sova)|urd[iî])|l(at(in[ao]?|vi(an?|e[sš]u))|ietuvi[uų]|ithuanian?)|m(a[ck]edon(ian?|ski)|agyar|alay(alam?|sian?)?|altese|andarin|arathi|elayu|ontenegro|ongol(ian?)|yanmar)|n(e(d|th)erlands?|epali|orw(ay|egian)|orsk( bokm[aå]l)?|ynorsk)|o(landese|dia)|p(ashto|ersi?an?|ol(n?isc?h|ski)|or?tugu?[eê]se?(( d[eo])? brasil(eiro)?| ?\(brasil\))?|unjabi)|r(om[aâi]ni?[aă]n?|um(ano|änisch)|ussi([ao]n?|sch))|s(anskrit|erbian|imple english|inha?la|lov(ak(ian?)?|enš?[cč]ina|en(e|ij?an?)|uomi)|erbisch|pagnolo?|panisc?h|rbeska|rpski|venska|c?wedisc?h|hqip)|t(a(galog|mil)|elugu|hai(land)?|i[eế]ng vi[eệ]t|[uü]rk([cç]e|isc?h|iş|ey))|u(rdu|zbek)|v(alencia(no?)?|ietnamese)|welsh|(англиис|[kк]алмыкс|[kк]азахс|немец|[pр]усс|[yу]збекс)кий( язык)??|עברית|[kкқ](аза[кқ]ша|ыргызча|ирилл)|українськ(а|ою)|б(еларуская|ългарски( език)?)|ελλ[ηι]νικ(ά|α)|ქართული|हिन्दी|ไทย|[mм]онгол(иа)?|([cс]рп|[mм]акедон)ски|العربية|日本語|한국(말|어)|‌हिनद़ि|বাংলা|ਪੰਜਾਬੀ|मराठी|ಕನ್ನಡ|اُردُو|தமிழ்|తెలుగు|ગુજરાતી|فارسی|پارسی|മലയാളം|پښتو|မြန်မာဘာသာ|中文(简体|繁體)?|中文（(简体?|繁體)）|简体|繁體)( language)?$',term): #filter 8
        return 'language as term'
    if re.search(u'\bneuke?n?\b|\bwtf\b|\bass(hole|wipe|\b)|bitch|\bcocks?\b|\bdicks?\b|\bloo?ser|\bcunts?\b|dildo|douche|fuck|nigg(er|a)|pedophile|\bfag(g|\b)|penis|blowjob|\bcrap|\bballs|sluts?\b|\btrolo?l|whore|racist|\bsuck|\bshit|\bgays?\b|\bblah|\bpuss(y|ies?)|\bawesome\b|\bpo{2,}p?\b|\bidiots?\b|\bretards?\b|\byolo\b|\b(my|ya|y?our|his|her) m(ama|om|other)|vaginas?\b|\bswag\b',term.lower()): #filter 11
        if 'ballspieler' not in term.lower():
            return 'bad word'
    if re.search(u'^(ahoj|h[ae]lo|hej|hi|hola|привет)$',term.lower()): #filter 47
        return 'hello!'
    if re.search(u'(\w\w\w)\1{1,}',term):
        if 'cantant' not in term.lower():
            return 'repetition'
    if re.search(u'(..)\1{2,}',term):
        return 'repetition'
    if re.search(u'(.)\1{3,}',term):
        return 'repetition'
    return 0

def ifPatrolled(title,timestamp): #find method without timestamp
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rcprop': 'title',
        'rcshow': '!patrolled',
        'rcstart': timestamp,
        'rcend': timestamp,
        'rclimit' : 500,
        'rcnamespace':0,
    }
    req = api.Request(site=site, parameters=params)
    data = req.submit()
    for m in data['query']['recentchanges']:
        if title == m['title']:
            return 0
    return 1
    

def ifInUse(q,term,termtype,lang):
    if termtype=='alias':
        termtype='aliases'
    else:
        termtype+='s'
    item = pywikibot.ItemPage(repo,q)
    if item.isRedirectPage():
        return 0
    if not item.exists():
        return 0
    dict = item.get()
    if termtype in dict:
        if lang in dict[termtype]:
            if dict[termtype][lang] == term:
                return 1
    return 0

def ifFalsePositive(q,term,lang):
    try:
        item = pywikibot.ItemPage(repo,q)
        if item.exists():
            dict = item.get()
            if 'sitelinks' in dict:
                for nn in dict['sitelinks']:
                    if dict['sitelinks'][nn] == term:
                        return 1
                if lang+'wiki' in dict['sitelinks']:
                    site2 = pywikibot.Site(lang, "wikipedia")
                    page2 = pywikibot.Page(site2, dict['sitelinks'][lang+'wiki'])
                    text = re.sub(u'\[\[[^\]]+\|','',page2.get())
                    text = re.sub(u'\[\[|\]\]','',text)
                    if term in text:
                        return 1
    except:
        pass
    return 0
    
def oldEdits():
    global text
    page2 = pywikibot.Page(site, 'User:Pasleim/Vandalism')
    oldtext = page2.get()
    foo = oldtext.split('\n')
    for line in foo:
        if '| [[Q' in line:
            res = re.search(u'\[\[Q([0-9]*)\]\] (.*) <nowiki>(.*)</nowiki> \|\| (add|edit) (label|description|alias) \|\| (.*) \|\| (.*) \|\| (.*) \|\| (.*)',line)
            if res:
                q = res.group(1)
                term = res.group(3)
                termtype = res.group(5)
                lang = res.group(6)
                timestamp = res.group(9)
                if ifInUse('Q'+str(q),term,termtype,lang) == 0:
                    continue
                if ifPatrolled('Q'+str(q),timestamp) == 1:
                    continue
            text += '|-\n'+line+'\n'

def newEdits():
    global text
    f1 = open('reports/vandalismTerms_time.dat','r')
    oldTime = f1.read().strip()
    f1.close()
    rccontinue = oldTime+'|0'
    while (1 == 1):
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|user|ids|timestamp',
            'rcstart': oldTime,
            'rcdir': 'newer',
            'rclimit' : 500,
            'rctype': 'edit',
            'rcnamespace':0,
            'rcshow' : '!patrolled',
            'rccontinue':rccontinue
        }
        req = api.Request(site=site, parameters=params)
        data = req.submit()
        for m in data['query']['recentchanges']:
            try:
                timestamp = m['timestamp']
                if 'comment' not in m:
                    continue
                if 'wbsetlabel' not in m['comment'] and 'wbsetdescription' not in m['comment'] and 'wbsetaliases' not in m['comment']:
                    continue
                foo = m['comment'].split(' */ ')
                term = foo[1].strip()
                meta = foo[0].split('|')
                lang = meta[1]
                if 'wbsetlabel' in m['comment']:
                    termtype = u'label'
                elif 'wbsetdescription' in m['comment']:
                    termtype = u'description'
                else:
                    termtype = u'alias'    
                result = filter(term,termtype,lang)
                if result == 0:
                    continue
                if ifInUse(m['title'],term,termtype,lang) == 0:
                    continue
                if result != 'URL':
                    if ifFalsePositive(m['title'],term,lang) == 1:
                        continue
                action = ''
                if '-set:' in meta[0]:
                    action = 'edit'
                elif '-add:' in meta[0]:
                    action = 'add'
                else:
                    continue
                text +=  u'|-\n| [['+m['title']+']] ([//www.wikidata.org/w/index.php?diff='+str(m['revid'])+' diff]) || <nowiki>'+term+'</nowiki> || '+action+' '+termtype+' || '+lang+' || '+result+' || {{user|'+m['user']+'}} || '+timestamp+'\n'
            except:
                print('error unkown')
        if 'query-continue' in data:
                rccontinue = data['query-continue']['recentchanges']['rccontinue']
        else:
            break
    text += '|}'
    f3 = open('reports/vandalismTerms_time.dat','w')
    f3.write(re.sub('\:|\-|Z|T','',timestamp))
    f3.close()
    page.put(text, summary='upd', minorEdit=False)

if __name__ == "__main__":
    oldEdits()
    newEdits()
