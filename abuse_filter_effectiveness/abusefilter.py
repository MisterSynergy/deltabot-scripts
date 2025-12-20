#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime
from pathlib import Path
from time import strftime

import mariadb
import pywikibot as pwb


HEADER = """Update: <onlyinclude>{update_timestamp}</onlyinclude>

{{| class="wikitable sortable plainlinks"
|-
!Id !! Description !! Active Since !! Just Warned !! Edited !! Warning Deterred
"""

FOOTER = """|}

[[Category:Wikidata statistics]]"""

TABLE_ROW = """|-
| [//wikidata.org/wiki/Special:AbuseLog?wpSearchFilter={af_id} {af_id}] || {title} || {start_date} || {warned} || {edited} || {deterred}%
"""

TS_FORMAT_MW = '%Y%m%d%H%M%S'


def make_report() -> str:
    query1 = 'SELECT af_id, CONVERT(af_public_comments USING utf8) AS af_public_comments FROM abuse_filter WHERE af_actions="warn,tag"'
    query2 = 'SELECT CONVERT(afh_timestamp USING utf8) AS afh_timestamp FROM abuse_filter_history WHERE afh_changed_fields LIKE "%actions%" AND afh_filter=%(afh_filter)s ORDER BY afh_timestamp DESC LIMIT 1'
    query3 = 'SELECT COUNT(*) AS cnt FROM abuse_filter_log WHERE afl_filter_id=%(afl_filter)s AND afl_actions=%(afl_actions)s AND afl_timestamp>%(afl_timestamp)s'

    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cur = db.cursor(dictionary=True)

    cur.execute(query1)
    result1 = cur.fetchall()

    text = ''
    for row in result1:
        af_id = row.get('af_id')
        comment = row.get('af_public_comments')
        if af_id is None or comment is None:
            continue

        cur.execute(query2, { 'afh_filter' : af_id })
        result2 = cur.fetchall()
        if len(result2) == 0:
            continue

        start = result2[0].get('afh_timestamp')
        if start is None:
            continue
        start_date_ts = datetime.strptime(start, TS_FORMAT_MW)

        cur.execute(query3, { 'afl_filter' : af_id, 'afl_actions' : 'warn', 'afl_timestamp' : start_date_ts.strftime(TS_FORMAT_MW) })
        result3a = cur.fetchall()
        warn = result3a[0].get('cnt')
        if warn is None:
            continue

        cur.execute(query3, { 'afl_filter' : af_id, 'afl_actions' : 'tag', 'afl_timestamp' : start_date_ts.strftime(TS_FORMAT_MW) })
        result3b = cur.fetchall()
        tag = result3b[0].get('cnt')
        if tag is None:
            continue

        if warn > 0:
            deterred = f'{(warn-tag)/warn*100:.1f}'
        else:
            deterred = '0'

        text += TABLE_ROW.format(
            af_id=af_id,
            title=comment,
            start_date=start_date_ts.strftime('%Y-%m-%d'),
            warned=warn-tag,
            edited=tag,
            deterred=deterred,
        )

    cur.close()
    db.close()

    return text


def main() -> None:
    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report() + FOOTER

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:Database reports/Abuse filter effectiveness')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
