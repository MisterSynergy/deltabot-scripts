# -*- coding: UTF-8 -*-

from datetime import date, timedelta
from pathlib import Path

import mariadb
import pywikibot as pwb
import requests


class Replica:
    def __init__(self) -> None:
        self.connection = mariadb.connect(
            host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
            database='wikidatawiki_p',
            default_file=str(Path.home() / 'replica.my.cnf'),
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.connection.close()


def main() -> None:
    response = requests.get(
        url='https://www.wikidata.org/w/index.php?title=Wikidata:WikiProject_Counter-Vandalism/plot1-csv&action=raw'
    )
    old_csv = response.text.split('\n')
    new_csv = ''

    oldest = date.today() - timedelta(31)
    newest = date.today() - timedelta(1)

    for line in old_csv:
        if 'unpatrolled edits' in line or 'IP' in line:
            continue
        if oldest.strftime('%Y/%m/%d') in line:
            continue
        new_csv += line.strip()+'\n'

    for dd in range(0,30):
        day = date.today() - timedelta(30-dd)

        query = 'SELECT COUNT(*) as cnt FROM recentchanges WHERE rc_patrolled=0 AND rc_timestamp>%(dayformat_start)s AND rc_timestamp<=%(dayformat_end)s'
        params = {
            'dayformat_start' : f'{day.strftime("%Y%m%d")}000000',
            'dayformat_end' : f'{day.strftime("%Y%m%d")}235959',
        }

        with Replica() as cur:
            cur.execute(query, params)
            result = cur.fetchall()

        for row in result:
            new_csv += f'{day.strftime("%Y/%m/%d")},{row.get("cnt", 0)},"unpatrolled edits"\n'

    query = """SELECT COUNT(*) AS patrols FROM logging WHERE log_action='patrol' AND log_params LIKE '%\"6::auto\";i:0%' AND log_timestamp>%(newestformat_start)s AND log_timestamp<=%(newestformat_end)s"""
    params = {
        'newestformat_start' : f'{newest.strftime("%Y%m%d")}000000',
        'newestformat_end' : f'{newest.strftime("%Y%m%d")}235959',
    }

    with Replica() as cur:
        cur.execute(query, params)
        result = cur.fetchall()

    for row in result:
        new_csv += f'{newest.strftime("%Y/%m/%d")},{row.get("patrols", 0)},"patrol actions"\n' 

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:WikiProject_Counter-Vandalism/plot1-csv')
    page.text = new_csv
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
