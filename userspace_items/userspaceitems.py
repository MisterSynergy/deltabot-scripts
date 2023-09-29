#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0


import MySQLdb
import pywikibot
from time import strftime


SITE = pywikibot.Site('wikidata', 'wikidata')
REPORT_PAGE = 'Wikidata:Database reports/User pages'
USERSPACE_NAMES_FILE = './reports/userspace_names.dat'

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
  ips_item_id,
  ips_site_page
FROM
  wb_items_per_site
WHERE
  ips_site_id="{site}"
  AND ips_site_page LIKE "{ns}:%"'''
DB_PARAMS = {
    'host' : 'wikidatawiki.analytics.db.svc.wikimedia.cloud',
    'db' : 'wikidatawiki_p',
    'read_default_file' : 'replica.my.cnf',
}

WHITELIST = [  # page titles containing any of these strings are acceptable
    'مستخدم:صندوق مستخدم/',  # arwiki
    'Vorlage',  # de
    'Userbox',  # en
    'User:UBX/',  # enwiki
    'کاربر:جعبه کاربر/',  # fawiki
    'Wikipedysta:Userboksy/',  # plwiki
]


def make_report(db_conn):
    text = ''
    with open(USERSPACE_NAMES_FILE, mode='r', encoding='utf8') as file_handle:
        for line in file_handle.readlines():
            dbname, group, lang, ns = line.strip().split('|')
            text += get_report(db_conn, dbname, group, lang, ns)

    return text


def is_userbox_template(page_title:str) -> bool:
    for term in WHITELIST:
        if term in page_title:
            return True

    return False


def get_report(db_conn, dbname:str, group:str, lang:str, ns:str) -> str:
    text = ''

    cursor = db_conn.cursor()
    query = QUERY.format(site=dbname, ns=ns)
    try:
        cursor.execute(query)
    except MySQLdb._exceptions.ProgrammingError as exception:
        print(exception, query)

    for row in cursor:
        try:
            qid_numerical, page_title = row
        except:
            continue

        page_title = page_title.decode('utf8')

        if is_userbox_template(page_title) is True:
            continue

        text += TABLE_ROW.format(
            qid_numerical=qid_numerical,
            group=group,
            lang=lang,
            page_title=page_title
        )

    cursor.close()

    return text


def main() -> None:
    db_conn = MySQLdb.connect(**DB_PARAMS)
    report = make_report(db_conn)

    page = pywikibot.Page(SITE, REPORT_PAGE)
    page.text = HEADER + report + FOOTER
    page.save(
        summary='Bot:Updating database report',
        minor=False
    )

    db_conn.close()


if __name__ == '__main__':
    main()
