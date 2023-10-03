#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
from time import strftime
from typing import Generator, Optional

import mariadb
import pywikibot as pwb

class Replica:
    def __init__(self) -> None:
        self.connection = mariadb.connect(
            host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
            database='wikidatawiki_p',
            default_file=f'{expanduser("~")}/replica.my.cnf',
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.connection.close()


def get_total_pages() -> Optional[int]:
    with Replica() as cur:
        query = 'SELECT COUNT(*) AS cnt FROM page WHERE page_namespace=0 AND page_is_redirect=0'
        cur.execute(query)

        result =  cur.fetchall()
        total =  result[0].get('cnt')

    return total


def get_languages() -> Generator[str, None, None]:
    with Replica() as cur:
        query = 'SELECT DISTINCT CONVERT(wbxl_language USING utf8) AS wbxl_language FROM wbt_text_in_lang'
        cur.execute(query)

        for row in cur.fetchall():
            lang = row.get('wbxl_language')
            if lang is None:
                continue

            yield lang


def get_label_counts(langs:list[str]) -> Generator[tuple[str, int], None, None]:
    with Replica() as cur:
        query = 'SELECT COUNT(*) AS cnt FROM wbt_item_terms LEFT JOIN wbt_term_in_lang ON wbit_term_in_lang_id=wbtl_id LEFT JOIN wbt_type ON wbtl_type_id=wby_id LEFT JOIN wbt_text_in_lang ON wbtl_text_in_lang_id=wbxl_id WHERE wby_name="label" AND wbxl_language=%(lang)s'
        for lang in langs:
            params = { 'lang' : lang }
            cur.execute(query, params)

            for row in cur.fetchall():
                cnt = row.get('cnt')
                if cnt is None:
                    continue

                yield lang, cnt


def get_description_counts(langs:list[str]) -> Generator[tuple[str, int], None, None]:
    with Replica() as cur:
        query = 'SELECT COUNT(*) AS cnt FROM wbt_item_terms LEFT JOIN wbt_term_in_lang ON wbit_term_in_lang_id=wbtl_id LEFT JOIN wbt_type ON wbtl_type_id=wby_id LEFT JOIN wbt_text_in_lang ON wbtl_text_in_lang_id=wbxl_id WHERE wby_name="description" AND wbxl_language=%(lang)s'
        for lang in langs:
            params = { 'lang' : lang }
            cur.execute(query, params)

            for row in cur.fetchall():
                cnt = row.get('cnt')
                if cnt is None:
                    continue

                yield lang, cnt


def get_alias_counts(langs:list[str]) -> Generator[tuple[str, int, int], None, None]:
    with Replica() as cur:
        query = 'SELECT COUNT(*) AS cnt, COUNT(DISTINCT(wbit_item_id)) AS cnt_distinct FROM wbt_item_terms LEFT JOIN wbt_term_in_lang ON wbit_term_in_lang_id=wbtl_id LEFT JOIN wbt_type ON wbtl_type_id=wby_id LEFT JOIN wbt_text_in_lang ON wbtl_text_in_lang_id=wbxl_id WHERE wby_name="alias" AND wbxl_language=%(lang)s'
        for lang in langs:
            params = { 'lang' : lang }
            cur.execute(query, params)

            for row in cur.fetchall():
                cnt = row.get('cnt')
                cnt_distinct = row.get('cnt_distinct')
                if cnt is None or cnt_distinct is None:
                    continue

                yield lang, cnt, cnt_distinct


def make_header(total:int) -> str:
    text = f'Update: <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>.\n\n'
    text += f'Total items: {total:,}\n\n'
    text += '== Number of labels, descriptions and aliases for items per language ==\n'
    text += '{| class="wikitable sortable"\n|-\n! Language code\n! Language (English)\n! Language (native)\n! data-sort-type="number"|# of labels\n! data-sort-type="number"|# of descriptions\n! data-sort-type="number"|# of aliases\n! data-sort-type="number"|# of items with aliases\n'

    return text


def make_footer(text:str) -> str:
    text += '|}\n\n[[Category:Wikidata statistics|Language statistics]]'

    return text


def make_report(text:str, total:int, collect:dict[str, dict[str, int]]) -> str:
    for lang in sorted(collect):
        text += f'|-\n| {lang} || {{{{#language:{lang}|en}}}} || {{{{#language:{lang}}}}}\n| '

        if 'label' in collect[lang]:
            text += f'{collect[lang]["label"]:,} ({round(collect[lang]["label"]/total*100, 1)}%)'

        text += ' || '

        if 'description' in collect[lang]:
            text += f'{collect[lang]["description"]:,} ({round(collect[lang]["description"]/total*100, 1)}%)'

        text += '\n| '

        if 'alias' in collect[lang]:
            text += f'{collect[lang]["alias"]:,} || {collect[lang]["items_with_alias"]:,}'
        else:
            text += ' || '

        text += '\n'

    return text


def write_to_wiki(text:str) -> None:
    if len(text) <= 1000:  # TODO: why necessary?
        return

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Language statistics for items')
    page.text = text
    page.save(summary='upd', minor=False)


def main() -> None:
    total = get_total_pages()
    if total is None:
        return

    collect:dict[str, dict[str, int]] = {}

    #get languages
    for lang in get_languages():
        collect[lang] = {}

    #get labels
    for lang, cnt in get_label_counts(list(collect.keys())):
        collect[lang]['label'] = cnt

    #get descriptions
    for lang, cnt in get_description_counts(list(collect.keys())):
        collect[lang]['description'] = cnt

    #get aliases
    for lang, cnt, cnt_distinct in get_alias_counts(list(collect.keys())):
        collect[lang]['alias'] = cnt
        collect[lang]['items_with_alias'] = cnt_distinct

    text = make_header(total)
    text = make_report(text, total, collect)
    text = make_footer(text)

    write_to_wiki(text)


if __name__=='__main__':
    main()
