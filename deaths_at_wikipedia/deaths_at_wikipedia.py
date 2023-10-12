#!/usr/bin/python
# -*- coding: UTF-8 -*-

from dataclasses import dataclass
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
import sys
from time import sleep, strftime
from typing import Any, Generator, Optional

import pywikibot as pwb
import requests


PROJECTS:list[dict[str, Any]] = [
    {'wiki' : 'ar', 'prefix' : 'وفيات '},
    {'wiki' : 'az', 'suffixes': [ '-ci ildə vəfat edənlər', '-cı ildə vəfat edənlər', '-cü ildə vəfat edənlər', '-cu ildə vəfat edənlər' ]},
    {'wiki' : 'be', 'prefix' : 'Памерлі ў ', 'suffix': ' годзе'},
    {'wiki' : 'bg', 'prefix' : 'Починали през ', 'suffix': ' година'},
    {'wiki' : 'ca', 'prefix' : 'Morts el '},
    {'wiki' : 'cs', 'prefix' : 'Úmrtí '},
    {'wiki' : 'commons', 'suffix' : '_deaths'},
    {'wiki' : 'cy', 'prefix' : 'Marwolaethau '},
    {'wiki' : 'da', 'prefix' : 'Døde i '},
    {'wiki' : 'de', 'prefix' : 'Gestorben '},
    {'wiki' : 'el', 'prefix' : 'Θάνατοι το '},
    {'wiki' : 'en', 'suffix' : ' deaths'},
    {'wiki' : 'eo', 'prefix' : 'Mortintoj en '},
    {'wiki' : 'es', 'prefix' : 'Fallecidos en '},
    {'wiki' : 'et', 'prefix' : 'Surnud '},
    {'wiki' : 'eu', 'suffixes': [ 'eko heriotzak', 'ko heriotzak' ]},
    {'wiki' : 'fi', 'prefix' : 'Vuonna ', 'suffix': ' kuolleet'},
    {'wiki' : 'fr', 'prefixes' : [ 'Décès en ', 'Décès en janvier ', 'Décès en février ', 'Décès en mars ', 'Décès en avril ', 'Décès en mai ', 'Décès en juin ', 'Décès en juillet ', 'Décès en août ', 'Décès en septembre ', 'Décès en octobre ', 'Décès en novembre ', 'Décès en décembre ' ]},
    {'wiki' : 'gl', 'prefix' : 'Finados en '},
    {'wiki' : 'hu', 'suffixes': [ '-ban elhunyt személyek', '-ben elhunyt személyek' ]},
    {'wiki' : 'hy', 'suffix': ' մահեր'},
    {'wiki' : 'id', 'prefix' : 'Kematian '},
    {'wiki' : 'it', 'prefix' : 'Morti nel '},
    {'wiki' : 'ja', 'suffix': '年没'},
    {'wiki' : 'ka', 'prefix' : 'გარდაცვლილი '},
    {'wiki' : 'kk', 'suffix': ' жылы қайтыс болғандар'},
    {'wiki' : 'ko', 'suffix': '년 죽음'},
    {'wiki' : 'la', 'prefix' : 'Mortui '},
    {'wiki' : 'lb', 'prefix' : 'Gestuerwen '},
    {'wiki' : 'mk', 'prefix' : 'Починати во ', 'suffix': ' година'},
    {'wiki' : 'ms', 'prefix' : 'Kematian '},
    {'wiki' : 'nn', 'prefix' : 'Døde i '},
    {'wiki' : 'no', 'prefix' : 'Dødsfall i '},
    {'wiki' : 'pl', 'prefix' : 'Zmarli w '},
    {'wiki' : 'pt', 'prefix' : 'Mortos em '},
    {'wiki' : 'ro', 'prefix' : 'Decese în '},
    {'wiki' : 'ru', 'prefix' : 'Умершие в ', 'suffix': ' году'},
    {'wiki' : 'sco', 'suffix': ' daiths'},
    {'wiki' : 'sh', 'prefix' : 'Umrli ', 'suffix': '.'},
    {'wiki' : 'simple', 'suffix' : ' deaths'},
    {'wiki' : 'sk', 'prefix' : 'Úmrtia v '},
    {'wiki' : 'sl', 'prefix' : 'Umrli leta '},
    {'wiki' : 'sr', 'prefix' : 'Умрли '},
    {'wiki' : 'sv', 'prefix' : 'Avlidna '},
    {'wiki' : 'ta', 'suffix' : ' இறப்புகள்'},
    {'wiki' : 'th', 'prefix' :'บุคคลที่เสียชีวิตในปี พ.ศ. '},
    {'wiki' : 'tr', 'suffix': ' yılında ölenler'},
    {'wiki' : 'uk', 'prefix' : 'Померли '},
    {'wiki' : 'ur', 'prefix' : 'ء کی وفیات'},
    {'wiki' : 'vi', 'prefix' : 'Mất '},
    {'wiki' : 'zh', 'suffix' : '年逝世'},
    {'wiki' : 'zh_min_nan', 'suffix' : ' nî kòe-sin'},
]    
NONROMAN_LANG = [ 'ja', 'zh', 'ar', 'ru', 'uk', 'fa', 'ko', 'hy', 'el', 'th', 'ta', 'mr', 'kk', 'mk', 'sr', 'be', 'bg', 'ur', 'zh_min_nan', 'ka' ]
CYR_LANG = [ 'ru', 'uk', 'sr', 'mk', 'kk', 'bg', 'be' ]

HEADER = """Persons deceased in {year} according to Wikipedia, but without {{{{P|570}}}} at Wikidata. Data as of {timestamp}.

{{{{Wikidata:Database reports/Deaths at Wikipedia/header-year}}}}<onlyinclude>
"""

FOOTER = """</onlyinclude></table>

[[Category:Database reports deaths by year|{year}]]__NOINDEX__"""

TABLE_ROW = """{{{{tr peoplelist 4|{qid}|{wikis}|{timestamp}|{label}|{row_count}}}}}
"""

STAT = '{{{{DR rd numbers-1|year={year}|items={items}|latest={latest}|en={enwiki}|nonroman={nonroman_wiki}|cyr={cyr_wiki}|ar={arwiki}|ja={jawiki}|zh={zhwiki}|24h={days1}|48h={days2}|7d={days7}|30d={days30}|365dp={days365p}}}}}'

SUMMARY_ROW = """{{{{DR rd numbers-y|year={year}|items={items}|latest={latest}|en={enwiki}|nonroman={nonroman_wiki}|cyr={cyr_wiki}|ar={arwiki}|ja={jawiki}|zh={zhwiki}|24h={days1}|48h={days2}|7d={days7}|30d={days30}|365dp={days365p}|earliest={earliest}}}}}
"""

SITE = pwb.Site('wikidata', 'wikidata')
EDIT_SUMMARY_TEMPLATE = 'Bot: Updating Database report: {items} items; latest: {latest}; en: {enwiki}; nonroman: {nonroman_wiki}; ar: {arwiki}, ja: {jawiki}, zh: {zhwiki}, cyr: {cyr_wiki}; AGING 24h: {days1}, 48h: {days2}, 7d: {days7}, 30d: {days30},  365+d: {days365p}'
EDIT_SUMMARY_ALL_TEMPLATE = 'Bot: Updating Database report {years} years: {items} items; latest: {all_latest}; en: {enwiki}; nonroman: {nonroman_wiki}; ar: {arwiki}, ja: {jawiki}, zh: {zhwiki}, cyr: {cyr_wiki}; AGING 24h: {days1}, 48h: {days2}, 7d: {days7},  30d: {days30},  365+d: {days365p}'

USER_AGENT = f'{requests.utils.default_user_agent()} (deaths_at_wikipedia.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WD = 'http://www.wikidata.org/entity/'
PETSCAN_ENDPOINT = 'https://petscan.wmflabs.org/'
PETSCAN_SLEEP = 1

TS_FORMAT_OUT = '%Y-%m-%d, %H:%M:%S'
TS_FORMAT_HEADER = '%Y-%m-%d %H:%M (%Z)'
TS_FORMAT_MW = '%Y%m%d%H%M%S'

TODAY = datetime.now()
YEARS = list(range(1941, TODAY.year+1))


@dataclass
class PetscanRow:
    page_id : int
    page_title : str
    page_namespace : int
    page_namespace_text : str
    qid : str
    page_len : int
    page_touched : datetime


def query_petscan(payload:dict[str, str]) -> Generator[PetscanRow, None, None]:
    response = requests.post(
        url=PETSCAN_ENDPOINT,
        data=payload,
        headers={ 'User-Agent' : USER_AGENT }
    )
    sleep(PETSCAN_SLEEP)

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse petscan response as JSON; HTTP status {response.status_code}; time elapsed {response.elapsed.total_seconds():.2f} s') from exception

    if len(data.get('*', [])) != 1:
        return

    for row in data.get('*', [])[0].get('a', {}).get('*', []):
        yield PetscanRow(
            row.get('id'),
            row.get('title').replace('_', ' '),
            row.get('namespace'),
            row.get('nstext'),
            row.get('q'),
            row.get('len'),
            datetime.strptime(row.get('touched'), TS_FORMAT_MW),
        )


def query_wdqs(query:str) -> Generator[dict[str, Any], None, None]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': USER_AGENT,
        }
    )

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse WDQS response as JSON; HTTP status {response.status_code}; query time {response.elapsed.total_seconds:.2f} sec') from exception

    for row in data.get('results', {}).get('bindings', []):
        yield row


def thai_year(year:int) -> int:
    return year+543


def make_categories_list(year:int, prefix:Optional[str]=None, suffix:Optional[str]=None, prefixes:Optional[list[str]]=None, suffixes:Optional[list[str]]=None) -> list[str]:
    if prefix is not None:
        if suffix is not None:
            return [ f'{prefix}{year}{suffix}' ]
        if suffixes is not None:
            return [ f'{prefix}{year}{suffix}' for suffix in suffixes ]
        return [ f'{prefix}{year}' ]

    if prefixes is not None:
        if suffix is not None:
            return [ f'{prefix}{year}{suffix}' for prefix in prefixes ]
        if suffixes is not None: # this can quickly become messy
            return [ f'{prefix}{year}{suffix}' for prefix in prefixes for suffix in suffixes ]
        return [ f'{prefix}{year}' for prefix in prefixes ]

    if suffix is not None:
        return [ f'{year}{suffix}' ]

    if suffixes is not None:
        return [ f'{year}{suffix}' for suffix in suffixes ]

    raise RuntimeWarning('No input received to build categories list')


def query_for_report(year:int) -> list[tuple[str, list[str], datetime]]:
    results:dict[str, dict[str, Any]] = {}
    for project in PROJECTS:
        project_code = project.get('wiki')
        if project_code is None:
            continue

        year_repr = year
        if project_code == 'th':
            year_repr = thai_year(year)

        family, ns = 'wikipedia', 0
        if project_code == 'commons':
            family, ns = 'wikimedia', 14

        categories = make_categories_list(
            year_repr,
            prefix=project.get('prefix'),
            suffix=project.get('suffix'),
            prefixes=project.get('prefixes'),
            suffixes=project.get('suffixes'),
        )

        payload = {
            'project' : family,
            'language' : project_code,
            'combination' : 'union',
            'categories' : '\n'.join(categories),
            f'ns[{ns}]' : '1',
            'wikidata_item' : 'with',
            'wikidata_prop_item_use' : 'P570',
            'wpiu' : 'none',
            'doit' : 'doit',
            'format' : 'json',
        }

        try:
            results_gen = query_petscan(payload)
        except RuntimeError as exception:
            print(exception)
            continue

        for row in results_gen:
            if row.qid not in results:
                results[row.qid] = {
                    'wiki_list' : [],
                    'touch_timestamp' : None,
                }

            results[row.qid]['wiki_list'].append(project_code)
            if results[row.qid]['touch_timestamp'] is None:
                results[row.qid]['touch_timestamp'] = row.page_touched
            else:
                results[row.qid]['touch_timestamp'] = min(results[row.qid]['touch_timestamp'], row.page_touched)

    return_results:list[tuple[str, list[str], datetime]] = []
    for qid, dct in results.items():
        return_results.append(
            (
                qid,
                dct['wiki_list'],
                dct['touch_timestamp'],
            )
        )

    return return_results


def get_list_of_human_qids(qids:list[str|None]) -> dict[str, str]:
    query = f"""SELECT DISTINCT ?item ?itemLabel ?label_sample (SAMPLE(?lemma) AS ?lemma_sample) WITH {{
  SELECT ?item WHERE {{
    VALUES ?item {{
      wd:{' wd:'.join([ qid for qid in qids[:5000] if qid is not None ])}
    }}
    ?item p:P31/ps:P31 wd:Q5 .
  }}
}} AS %subquery1 WITH {{
  SELECT ?item (SAMPLE(?label) AS ?label_sample) WHERE {{
    INCLUDE %subquery1 .
    OPTIONAL {{ ?item rdfs:label ?label }}
  }} GROUP BY ?item
}} AS %subquery2 WHERE {{
  INCLUDE %subquery2 .
  OPTIONAL {{ ?item ^schema:about/schema:name ?lemma }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en' }}
}} GROUP BY ?item ?itemLabel ?label_sample"""

    human_qids:dict[str, str] = {}
    for row in query_wdqs(query):
        human_qid = row.get('item', {}).get('value', '').replace(WD, '')

        label_en = row.get('itemLabel', {}).get('value', '')
        label_sample = row.get('label_sample', {}).get('value', '')
        label_lemma = row.get('lemma_sample', {}).get('value', '')
        if label_en not in [ '', human_qid ]:
            label = label_en
        elif label_sample != '':
            label = label_sample
        elif label_lemma != '':
            label = label_lemma
        else:
            label = human_qid

        human_qids[human_qid] = label

    return human_qids


def make_report(year:int) -> tuple[str, datetime, datetime, dict[str, int]]:
    result = query_for_report(year)

    report = ''
    latest = datetime.strptime('19700101000000', TS_FORMAT_MW)
    counts = {
        'items' : 0,
        'enwiki' : 0,
        'zhwiki' : 0,
        'arwiki' : 0,
        'jawiki' : 0,
        'days1' : 0,
        'days2' : 0,
        'days7' : 0,
        'days30' : 0,
        'days365p' : 0,
        'nonroman_wiki' : 0,
        'cyr_wiki' : 0,
    }

    list_of_humans = get_list_of_human_qids([ row[0] for row in result ])

    for row in result:
        qid, wiki_list, timestamp = row
        wikis = ','.join(wiki_list)

        if qid is None or len(wikis)==0 or timestamp is None:
            continue

        qid = qid.upper()

        human = (qid in list_of_humans.keys())
        if human is False:
            continue

        label = list_of_humans.get(qid)
        if label is None or len(label)==0:
            label = qid

        counts['items'] += 1
        if counts.get('items') == 1:
            earliest = timestamp

        if timestamp > latest:
            latest = timestamp

        if 'commons,' in wikis:
            wikis = wikis.replace('commons,', '') + ',commons'

        if ',en' in wikis:
            wikis= 'en,' + wikis.replace(',en', '', 1)

        report += TABLE_ROW.format(
            qid=qid,
            wikis=wikis,
            timestamp=timestamp.strftime(TS_FORMAT_OUT),
            label=label,
            row_count=counts.get('items')
        )

        if 'en' in wikis:
            counts['enwiki'] += 1
        if 'ar' in wikis:
            counts['arwiki'] += 1
        if 'ja' in wikis:
            counts['jawiki'] += 1
        if 'zh' in wikis:
            counts['zhwiki'] += 1

        if any(x in wikis for x in NONROMAN_LANG):
            counts['nonroman_wiki'] +=1
        if any(x in wikis for x in CYR_LANG):
            counts['cyr_wiki'] +=1

        if timestamp > (TODAY-timedelta(days=1)):
            counts['days1'] +=1
        if timestamp > (TODAY-timedelta(days=2)):
            counts['days2'] +=1
        if timestamp > (TODAY-timedelta(days=7)):
            counts['days7'] +=1
        if timestamp > (TODAY-timedelta(days=30)):
            counts['days30'] +=1
        if timestamp < (TODAY-timedelta(days=365)):
            counts['days365p'] +=1

    text = STAT.format(
        year=year,
        latest=latest.strftime(TS_FORMAT_OUT),
        **counts,
    )
    text += HEADER.format(year=year, timestamp=strftime(TS_FORMAT_HEADER)) 
    text += report
    text += FOOTER.format(year=year)

    edit_summary = EDIT_SUMMARY_TEMPLATE.format(
        latest=latest.strftime(TS_FORMAT_OUT),
        **counts,
    )

    page = pwb.Page(SITE, f'Wikidata:Database reports/Deaths at Wikipedia/{year}')
    page.text = text
    page.save(summary=edit_summary, minor=False)

    return text, earliest, latest, counts


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] != 'all':
        year = int(sys.argv[1])
        make_report(year)
        return

    years = 0
    all_summary = ''
    all_latest = datetime.strptime('19700101000000', TS_FORMAT_MW)
    all_counts = {}

    for year in YEARS:
        years += 1

        _, earliest, latest, counts = make_report(year)
        for key in counts.keys():
            if key not in all_counts:
                all_counts[key] = 0

            all_counts[key] += counts.get(key, 0)

        if latest > all_latest:
            all_latest = latest

        all_summary += SUMMARY_ROW.format(
            year=year,
            earliest=earliest.strftime(TS_FORMAT_OUT),
            latest=latest.strftime(TS_FORMAT_OUT),
            **counts
        )

    text = f"""{{{{Wikidata:Database reports/Deaths at Wikipedia/header}}}}
{all_summary}</table>

[[Category:Database reports deaths by year| ]]"""
    edit_summary = EDIT_SUMMARY_ALL_TEMPLATE.format(
        years=years,
        all_latest=all_latest.strftime(TS_FORMAT_OUT),
        **all_counts,
    )

    page = pwb.Page(SITE, 'Wikidata:Database reports/Deaths at Wikipedia')
    page.text = text
    page.save(summary=edit_summary, minor=False)


if __name__=='__main__':
    main()
