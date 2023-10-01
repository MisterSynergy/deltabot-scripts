#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
from time import strftime

import mariadb
import pywikibot


SITE = pywikibot.Site('wikidata', 'wikidata')
REPORT_PAGE = 'Wikidata:Database reports/User pages'
USERSPACE_NAMES_FILE = f'{expanduser("~")}/jobs/userspace_items/userspace_names.dat'

HEADER = f"""A list of pages with links to userspace. Update: <onlyinclude>{strftime('%Y-%m-%d %H:%M (%Z)')}</onlyinclude>

{{| class="wikitable sortable plainlinks" style="width: 100%; margin: auto;"
|- style="white-space: nowrap;"
! Item !! Link
"""
FOOTER = """|}

[[Category:Wikidata statistics]]"""
TABLE_ROW = """|-
| [[Q{qid_numerical}]] || [[{group}:{lang}:{page_title}]]
"""

QUERY = '''SELECT
  ips_item_id AS qid_numerical,
  CONVERT(ips_site_page USING utf8) AS page_title
FROM
  wb_items_per_site
WHERE
  ips_site_id=%(dbname)s
  AND ips_site_page LIKE %(pagename)s'''
DB_PARAMS = {
    'host' : 'wikidatawiki.analytics.db.svc.wikimedia.cloud',
    'database' : 'wikidatawiki_p',
    'default_file' : f'{expanduser("~")}/replica.my.cnf',
}

WHITELIST = [  # page titles containing any of these strings are acceptable
    'مستخدم:صندوق مستخدم/',  # arwiki
    'Vorlage',  # de
    'Userbox',  # en
    'User:UBX/',  # enwiki
    'کاربر:جعبه کاربر/',  # fawiki
    'Wikipedysta:Userboksy/',  # plwiki
]


def make_report() -> str:
    conn = mariadb.connect(**DB_PARAMS)
    cur = conn.cursor(dictionary=True)

    text = ''
    with open(USERSPACE_NAMES_FILE, mode='r', encoding='utf8') as file_handle:
        for line in file_handle.readlines():
            dbname, group, lang, ns = line.strip().split('|')
            text += get_report(cur, dbname, group, lang, ns)

    cur.close()
    conn.close()

    return text


def is_userbox_template(page_title:str) -> bool:
    for term in WHITELIST:
        if term in page_title:
            return True

    return False


def get_report(cur, dbname:str, group:str, lang:str, ns:str) -> str:
    text = ''
    
    params = { 'dbname' : dbname, 'pagename' : f'{ns}:%' }
    try:
        cur.execute(QUERY, params)
    except mariadb.ProgrammingError as exception:
        print(exception, params)

    for row in cur:
        qid_numerical = row.get('qid_numerical')
        page_title = row.get('page_title')

        if qid_numerical is None or page_title is None:
            continue

        if is_userbox_template(page_title) is True:
            continue

        text += TABLE_ROW.format(
            qid_numerical=qid_numerical,
            group=group,
            lang=lang,
            page_title=page_title
        )

    return text


def main() -> None:
    page = pywikibot.Page(SITE, REPORT_PAGE)
    page.text = HEADER + make_report() + FOOTER
    page.save(summary='Bot:Updating database report', minor=False)


if __name__ == '__main__':
    main()
