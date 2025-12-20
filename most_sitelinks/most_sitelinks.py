#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from pathlib import Path
from time import strftime

import mariadb
import pywikibot as pwb


HEADER = 'A list of items with the most sitelinks. Data as of <onlyinclude>{update_timestamp}</onlyinclude>.\n\n{{| class="wikitable sortable" style="width:100%; margin:auto;"\n|-\n! Item !! Sitelinks\n'
TABLE_ROW = '|-\n| {{{{Q|{qid}}}}} || {cnt}\n'
FOOTER = '|}\n\n[[Category:Wikidata statistics|Most sitelinked items]] [[Category:Database reports|Most sitelinked items]]'


def make_report() -> str:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cur = db.cursor(dictionary=True)

    query = 'SELECT ips_item_id, COUNT(*) AS cnt FROM wb_items_per_site GROUP BY ips_item_id ORDER BY cnt DESC LIMIT 100'
    cur.execute(query)

    text = ''
    for row in cur:
        qid = row.get('ips_item_id')
        cnt = row.get('cnt')

        if qid is None or cnt is None:
            continue

        text += TABLE_ROW.format(qid=qid, cnt=cnt)

    cur.close()
    db.close()

    return text


def main() -> None:
    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report() + FOOTER

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:Database reports/Most sitelinked items')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__ == '__main__':
    main()

