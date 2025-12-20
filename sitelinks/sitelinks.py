# -*- coding: UTF-8 -*-
# licensed under MIT: http://opensource.org/licenses/MIT

from pathlib import Path
from time import strftime
from typing import Optional

import mariadb
import pywikibot as pwb


def get_total_count(cur) -> Optional[int]:
    cur.execute('SELECT COUNT(*) AS cnt FROM page WHERE page_namespace=0 AND page_is_redirect=0')
    blo = cur.fetchall()
    cnt = blo[0].get('cnt')

    return cnt


def get_all_links_count(cur) -> Optional[int]:
    cur.execute('SELECT COUNT(*) AS cnt FROM wb_items_per_site')
    blo = cur.fetchall()
    cnt = blo[0].get('cnt')

    return cnt


def get_project_and_family_counts(cur) -> tuple[dict[str, int], dict[str, int]]:
    project_counts:dict[str, int] = {}
    family_counts:dict[str, int] = {}

    cur.execute('SELECT CONVERT(ips_site_id USING utf8) AS ips_site_id, COUNT(*) AS cnt FROM wb_items_per_site GROUP BY ips_site_id ORDER BY ips_site_id')

    for row in cur.fetchall():
        dbname = row.get('ips_site_id')
        count = row.get('cnt')

        if dbname is None or count is None:
            continue

        project_counts[dbname] = count

        if 'voyage' in dbname:
            key = 'wikivoyage'
        elif 'source' in dbname:
            key = 'wikisource'
        elif 'quote' in dbname:
            key = 'wikiquote'
        elif 'news' in dbname:
            key = 'wikinews'
        elif 'books' in dbname:
            key = 'wikibooks'
        elif 'wiktionary' in dbname:
            key = 'wiktionary'
        elif 'versity' in dbname:
            key = 'wikiversity'
        elif dbname in [ 'metawiki', 'commonswiki', 'specieswiki', 'wikifunctionswiki', 'wikidatawiki', 'mediawikiwiki' ]:
            key = 'special'
        elif dbname in [ 'outreachwiki', 'incubatorwiki', 'wikimaniawiki', 'ruwikimedia', 'sewikimedia' ]:
            key = 'other'
        else:
            key = 'wikipedia'

        if key not in family_counts:
            family_counts[key] = 0

        family_counts[key] += count

    return project_counts, family_counts


def get_frequencies(cur) -> dict[int, int]:
    cur.execute('SELECT CONVERT(pp_value USING utf8) AS sitelink_count, COUNT(*) AS cnt FROM page_props WHERE pp_propname="wb-sitelinks" GROUP BY pp_value')

    frequency:dict[int, int] = {}

    for row in cur.fetchall():
        sitelink_count = int(row.get('sitelink_count'))
        count = row.get('cnt')

        if sitelink_count is None or count is None:
            continue

        if sitelink_count < 10:
            bin = sitelink_count
        elif sitelink_count < 100:
            bin = int(sitelink_count/10)*10
        else:
            bin = int(sitelink_count/100)*100

        if bin not in frequency:
            frequency[bin] = 0

        frequency[bin] += count

    return frequency


def get_sitelinks_per_project_table(project_counts:dict[str, int], all_links_count:int, total_count:int) -> str:
    text = """{| class="wikitable sortable" style="margin-right:50px;"
|+ Sitelinks per project
|-
! Project
! data-sort-type="number" | # of sitelinks
"""

    for dbname, count in project_counts.items():
        if 'voyage' in dbname:
            text += '|- style="background: Bisque"'
        elif 'source' in dbname:
            text += '|- style="background: LightCyan"'
        elif 'quote' in dbname:
            text += '|- style="background: MistyRose"'
        elif 'news' in dbname:
            text += '|- style="background: PaleGreen"'
        elif 'books' in dbname:
            text += '|- style="background: #E9DDAF"'
        elif 'wiktionary' in dbname:
            text += '|- style="background: #CCF9CC"'
        elif 'versity' in dbname:
            text += '|- style="background: #CFDBC5"'
        elif dbname in [ 'metawiki', 'commonswiki', 'specieswiki', 'wikifunctionswiki', 'wikidatawiki', 'mediawikiwiki' ]:
            text += '|- style="background: SkyBlue"'
        elif dbname in [ 'outreachwiki', 'incubatorwiki', 'wikimaniawiki', 'ruwikimedia', 'sewikimedia' ]:
            text += '|- style="background: Gray"'
        else:
            text += '|-'

        text += f'\n| {dbname} || {count:,}\n'

    text += f"""|-
! Total !! {all_links_count:,} ({round(all_links_count/total_count, 2)} per Item)
|}}"""

    return text


def get_summary_table(family_counts:dict[str, int]) -> str:
    text = f"""{{| class="wikitable sortable" style="margin-right:50px;"
|+ Sitelinks per family
|-
! Projects
! data-sort-type="number" | # of sitelinks
|-
| wikipedia || {family_counts['wikipedia']:,}
|- style="background: Bisque"
| wikivoyage || {family_counts['wikivoyage']:,}
|- style="background: LightCyan"
| wikisource || {family_counts['wikisource']:,}
|- style="background: MistyRose"
| wikiquote || {family_counts['wikiquote']:,}
|- style="background: PaleGreen"
| wikinews || {family_counts['wikinews']:,}
|- style="background: #E9DDAF"
| wikibooks || {family_counts['wikibooks']:,}
|- style="background: #CFDBC5"
| wikiversity || {family_counts['wikiversity']:,}
|- style="background: #CCF9CC"
| wiktionary || {family_counts['wiktionary']:,}
|- style="background: SkyBlue"
| special || {family_counts['special']:,}
|- style="background: Gray"
| other || {family_counts['other']:,}
|}}"""

    return text


def get_sitelinks_per_item_table(frequencies:dict[int, int]) -> str:
    text = """{| class="wikitable sortable"
|+ Sitelinks per item
|-
! data-sort-type="number" | sitelinks
! data-sort-type="number" | # of items"""

    for freq_bin in sorted(frequencies):
        text += f'\n|-\n| {freq_bin}'

        if freq_bin >= 10 and freq_bin < 100:
            text += f'-{freq_bin+9}'

        if freq_bin >= 100:
            text += f'-{freq_bin+99}'

        text += f' links || {frequencies[freq_bin]:,}'

    text += """
|}
"""

    return text


def main() -> None:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cur = db.cursor(dictionary=True)

    total_count = get_total_count(cur)
    all_links_count = get_all_links_count(cur)

    if total_count is None or all_links_count is None:
        return

    project_counts, family_counts = get_project_and_family_counts(cur)
    frequencies = get_frequencies(cur)

    cur.close()
    db.close()

    text = f"""Update: <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>.

Total items: {total_count:,}
    
== Number of sitelinks ==
{{|
|- style="vertical-align:top;"
|
{get_sitelinks_per_project_table(project_counts, all_links_count, total_count)}
|
{get_summary_table(family_counts)}
|
{get_sitelinks_per_item_table(frequencies)}
|}}

[[Category:Wikidata statistics|Sitelink statistics]]"""

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Sitelink statistics')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
