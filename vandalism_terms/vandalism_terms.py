#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
import re
from typing import Optional

import pywikibot
from pywikibot.data import api


SITE = pywikibot.Site("wikidata", "wikidata")
SITE.login()
REPO = SITE.data_repository()

REPORT_PAGE = 'User:Pasleim/Vandalism'
TIMESTAMP_FILENAME = f'{expanduser("~")}/jobs/vandalism_terms/vandalismTerms_time.dat'
LATIN_LANGUAGES = ['af','ak','an','ang','ast','ay','az','bar','bcl','bi','bm','br','bs','ca','cbk-zam','ceb','ch','chm','cho','chy','co','crh-latn','cs','csb','cy','da','de','diq','dsb','ee','eml','en','eo','es','et','eu','ff','fi','fit','fj','fo','fr','frp','frr','fur','fy','ga','gd','gl','gn','gsw','gv','ha','haw','ho','hr','hsb','ht','hu','hz','id','ie','ig','ik','ilo','io','is','it','jbo','jv','kab','kg','ki','kj','kl','kr','ksh','ku','kw','la','lad','lb','lg','li','lij','lmo','ln','lt','lv','map-bms','mg','mh','mi','min','ms','mt','mus','mwl','na','nah','nan','nap','nb','nds','nds-nl','ng','nl','nn','nov','nrm','nv','ny','oc','om','pag','pam','pap','pcd','pdc','pih','pl','pms','pt','qu','rm','rn','ro','roa-tara','rup','rw','sc','scn','sco','se','sg','sgs','sk','sl','sm','sn','so','sq','sr-el','ss','st','stq','su','sv','sw','szl','tet','tk','tl','tn','to','tpi','tr','ts','tum','tw','ty','uz','ve','vec','vi','vls','vo','vro','wa','war','wo','xh','yo','za','zea','zu']

TEXT_TEMPLATE = """The following unpatrolled items might be vandalised. Please either revert the edits or mark them as patrolled.

{| class="wikitable sortable plainlinks"
|-
! Item !! Term !! Action !! Language !! Filter !! User !! Timestamp
"""


def filter(term:str, termtype:str, lang:str) -> Optional[str]:
    if re.search('(\!\!|\?\?|\.\.|,,|\<|\>)', term):
        return 'punctuation'

    if re.search('[A-Z]{5,}', term):
        return 'upper case'

    if re.search('[0-9]{6,}', term):
        return 'long number'

    if re.search('(http|www|\:\/\/)', term.lower()):
        return 'URL'

    if re.search('(language\-|description|label|alias|jpg|svg|^test$)', term.lower()):
        return 'suspicious words'

    if re.search('^([b-df-hj-np-tv-xz]{2,6}|[aeiouy][b-df-hj-np-tv-xz][bcdfghjkmnpqstvwxz]{2,5}[aeiouy]?|[b-df-hj-np-tv-xz][bcdfghjkmnpqstvwxz]{3,5}[aeiouy])$', term): #filter 46
        return 'nonsense'

    if lang in LATIN_LANGUAGES:
        if len(term) < 4 and termtype=='description':
            return 'short description'
        if re.search('[\u4e00-\u9fff]+|[\u0400-\u0500]+', term): #chinese and cyrillic characters
            return 'wrong script'

    if re.search('^([ei]n )?(a(frikaa?ns|lbanian?|lemanha|ng(lais|ol)|ra?b(e?|[ei]c|ian?|isc?h)|rmenian?|ssamese|azeri|z[eə]rba(ijani?|ycan(ca)?|yjan)|нглийский)|b(ahasa( (indonesia|jawa|malaysia|melayu))?|angla|as(k|qu)e|[aeo]ng[ao]?li|elarusian?|okmål|osanski|ra[sz]il(ian?)?|ritish( kannada)?|ulgarian?)|c(ebuano|hina|hinese( simplified)?|zech|roat([eo]|ian?)|atal[aà]n?|рпски|antonese)|[cč](esky|e[sš]tina)|d(an(isc?h|sk)|e?uts?ch)|e(esti|ll[hi]nika|ng(els|le(ski|za)|lisc?h)|spa(g?[nñ]h?i?ol|nisc?h)|speranto|stonian|usk[ae]ra)|f(ilipino|innish|ran[cç](ais|e|ez[ao])|ren[cs]h|arsi|rancese)|g(al(ego|ician)|uja?rati|ree(ce|k)|eorgian|erman[ay]?|ilaki)|h(ayeren|ebrew|indi|rvatski|ungar(y|ian))|i(celandic|ndian?|ndonesian?|ngl[eê]se?|ngilizce|tali(ano?|en(isch)?))|ja(pan(ese)?|vanese)|k(a(nn?ada|zakh)|hmer|o(rean?|sova)|urd[iî])|l(at(in[ao]?|vi(an?|e[sš]u))|ietuvi[uų]|ithuanian?)|m(a[ck]edon(ian?|ski)|agyar|alay(alam?|sian?)?|altese|andarin|arathi|elayu|ontenegro|ongol(ian?)|yanmar)|n(e(d|th)erlands?|epali|orw(ay|egian)|orsk( bokm[aå]l)?|ynorsk)|o(landese|dia)|p(ashto|ersi?an?|ol(n?isc?h|ski)|or?tugu?[eê]se?(( d[eo])? brasil(eiro)?| ?\(brasil\))?|unjabi)|r(om[aâi]ni?[aă]n?|um(ano|änisch)|ussi([ao]n?|sch))|s(anskrit|erbian|imple english|inha?la|lov(ak(ian?)?|enš?[cč]ina|en(e|ij?an?)|uomi)|erbisch|pagnolo?|panisc?h|rbeska|rpski|venska|c?wedisc?h|hqip)|t(a(galog|mil)|elugu|hai(land)?|i[eế]ng vi[eệ]t|[uü]rk([cç]e|isc?h|iş|ey))|u(rdu|zbek)|v(alencia(no?)?|ietnamese)|welsh|(англиис|[kк]алмыкс|[kк]азахс|немец|[pр]усс|[yу]збекс)кий( язык)??|עברית|[kкқ](аза[кқ]ша|ыргызча|ирилл)|українськ(а|ою)|б(еларуская|ългарски( език)?)|ελλ[ηι]νικ(ά|α)|ქართული|हिन्दी|ไทย|[mм]онгол(иа)?|([cс]рп|[mм]акедон)ски|العربية|日本語|한국(말|어)|‌हिनद़ि|বাংলা|ਪੰਜਾਬੀ|मराठी|ಕನ್ನಡ|اُردُو|தமிழ்|తెలుగు|ગુજરાતી|فارسی|پارسی|മലയാളം|پښتو|မြန်မာဘာသာ|中文(简体|繁體)?|中文（(简体?|繁體)）|简体|繁體)( language)?$', term): #filter 8
        return 'language as term'

    if re.search('\bneuke?n?\b|\bwtf\b|\bass(hole|wipe|\b)|bitch|\bcocks?\b|\bdicks?\b|\bloo?ser|\bcunts?\b|dildo|douche|fuck|nigg(er|a)|pedophile|\bfag(g|\b)|penis|blowjob|\bcrap|\bballs|sluts?\b|\btrolo?l|whore|racist|\bsuck|\bshit|\bgays?\b|\bblah|\bpuss(y|ies?)|\bawesome\b|\bpo{2,}p?\b|\bidiots?\b|\bretards?\b|\byolo\b|\b(my|ya|y?our|his|her) m(ama|om|other)|vaginas?\b|\bswag\b', term.lower()): #filter 11
        if 'ballspieler' not in term.lower():
            return 'bad word'

    if re.search('^(ahoj|h[ae]lo|hej|hi|hola|привет)$', term.lower()): #filter 47
        return 'hello!'

    if re.search('(\w\w\w)\1{1,}', term):
        if 'cantant' not in term.lower():
            return 'repetition'

    if re.search('(..)\1{2,}', term):
        return 'repetition'

    if re.search('(.)\1{3,}', term):
        return 'repetition'

    return  None


def edit_is_patrolled(title:str, timestamp:str) -> bool: #find method without timestamp
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rcprop': 'title',
        'rcshow': '!patrolled',
        'rcstart': timestamp,
        'rcend': timestamp,
        'rclimit' : '500',
        'rcnamespace': '0',
    }
    request = api.Request(site=SITE, parameters=params)
    data = request.submit()

    for edit in data.get('query', {}).get('recentchanges', []):
        if title == edit.get('title'):
            return False

    return True


def edit_is_live(qid:str, term:str, termtype:str, lang:str) -> bool:
    if termtype=='alias':
        termtype='aliases'
    else:
        termtype+='s'

    item = pywikibot.ItemPage(REPO, qid)
    if item.isRedirectPage():
        return False
    if not item.exists():
        return False

    dct = item.get()
    if termtype not in dct:
        return False

    if lang not in dct[termtype]:
        return False

    if dct[termtype][lang]==term:
        return True

    return False


def edit_is_false_positive(qid:str, term:str, lang:str) -> bool:
    item = pywikibot.ItemPage(REPO, qid)
    if not item.exists():
        return False

    dct = item.get()
    if 'sitelinks' not in dct:
        return False

    for nn in dct['sitelinks']:
        if term in dct['sitelinks'][nn].title:
            return True

    if f'{lang}wiki' in dct['sitelinks']:
        sitelink = dct['sitelinks'][f'{lang}wiki']
        local_page = pywikibot.Page(sitelink)
        if not local_page.exists():
            return False

        text = re.sub('\[\[[^\]]+\|', '', local_page.text)
        text = re.sub('\[\[|\]\]', '', text)

        if term in text:
            return True

    return False


def old_edits(text:str) -> str:
    page = pywikibot.Page(SITE, REPORT_PAGE)
    old_text = page.get()

    for line in old_text.split('\n'):
        if '| [[Q' not in line:
            continue

        res = re.search('\[\[Q([0-9]*)\]\] (.*) <nowiki>(.*)</nowiki> \|\| (add|edit) (label|description|alias) \|\| (.*) \|\| (.*) \|\| (.*) \|\| (.*)', line)
        if not res:
            continue

        qid_numeric = res.group(1)
        term = res.group(3)
        termtype = res.group(5)
        lang = res.group(6)
        timestamp = res.group(9)

        if edit_is_live(f'Q{qid_numeric}', term, termtype, lang) is False:
            continue

        if edit_is_patrolled(f'Q{qid_numeric}', timestamp) is True:
            continue

        text += f'|-\n{line}\n'

    return text


def new_edits(text:str) -> str:
    with open(TIMESTAMP_FILENAME, mode='r', encoding='utf8') as file_handle:
        old_time = file_handle.read().strip()

    rccontinue = f'{old_time}|0'

    while True:
        params = {
            'action' : 'query',
            'list' : 'recentchanges',
            'rcprop' : 'title|comment|user|ids|timestamp',
            'rcstart' : old_time,
            'rcdir' : 'newer',
            'rclimit' : '500',
            'rctype': 'edit',
            'rcnamespace': '0',
            'rcshow' : '!patrolled',
            'rccontinue' : rccontinue,
        }
        request = api.Request(site=SITE, parameters=params)
        data = request.submit()
        for edit in data.get('query', {}).get('recentchanges', []):
            timestamp = edit.get('timestamp')

            comment = edit.get('comment')
            if comment is None:
                continue

            if 'wbsetlabel' not in comment and 'wbsetdescription' not in comment and 'wbsetaliases' not in comment:
                continue

            magic_edit_summary = comment.split(' */ ')
            if len(magic_edit_summary) < 2:
                continue

            term = magic_edit_summary[1].strip()
            meta = magic_edit_summary[0].split('|')
            lang = meta[1]
            if 'wbsetlabel' in comment:
                termtype = 'label'
            elif 'wbsetdescription' in comment:
                termtype = 'description'
            else:
                termtype = 'alias'    

            result = filter(term, termtype, lang)

            if result is None:
                continue

            if edit_is_live(edit['title'], term, termtype, lang) is False:
                continue

            if result != 'URL':
                if edit_is_false_positive(edit['title'], term, lang) is True:
                    continue

            action = ''

            if '-set:' in meta[0]:
                action = 'edit'
            elif '-add:' in meta[0]:
                action = 'add'
            else:
                continue

            text +=  f'|-\n| [[{edit.get("title", "")}]] ([//www.wikidata.org/w/index.php?diff={edit.get("revid", 0)} diff]) || <nowiki>{term}</nowiki> || {action} {termtype} || {lang} || {result} || {{{{user|{edit.get("user", "")}}}}} || {timestamp}\n'

        rccontinue = data.get('continue', {}).get('rccontinue')
        if rccontinue is None:
            break

    text += '|}'

    with open(TIMESTAMP_FILENAME, mode='w', encoding='utf8') as file_handle:
        file_handle.write(re.sub('\:|\-|Z|T', '', timestamp))

    return text


def write_to_wiki(wikitext:str) -> None:
    page = pywikibot.Page(SITE, REPORT_PAGE)
    page.text = wikitext
    page.save(summary='upd', minor=False)


def main() -> None:
    write_to_wiki(new_edits(old_edits(TEXT_TEMPLATE)))


if __name__ == '__main__':
    main()
