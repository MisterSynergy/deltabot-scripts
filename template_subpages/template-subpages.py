#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
import mariadb
import pywikibot as pwb


def main() -> None:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf'
    )
    cur = db.cursor(dictionary=True)
    
    query = """SELECT
    ips_item_id,
    ips_site_page
FROM
    wb_items_per_site
WHERE
    (
        ips_site_page LIKE '%/doc'
        OR ips_site_page LIKE '%/sandbox'
        OR ips_site_page LIKE '%/testcases'
        OR ips_site_page LIKE '%/TemplateData'
        OR ips_site_page LIKE '%/dok'
        OR ips_site_page LIKE '%/belge'
        OR ips_site_page LIKE '%/Spielwiese'
        OR ips_site_page LIKE '%/شرح'
    )
    AND ips_site_page NOT LIKE 'Wiki%'"""

    cur.execute(query)

    text = f'Found {cur.rowcount} items\n\n'
    text += '== Items with sitelinks /doc, /dok, /belge, /sandbox, /testcases, /TemplateData, /شرح ==\n'

    for row in cur.fetchall():
        text += f'* {row.get("ips_site_page", "")}: [[Q{row.get("ips_item_id", "")}]]\n'

    cur.close()
    db.close()

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Unsupported sitelinks')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
