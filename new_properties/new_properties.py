# !/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import re
import mwparserfromhell
import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

HEADER_PROPERTIES = '<!-- NEW PROPERTIES DO NOT REMOVE -->'
FOOTER_PROPERTIES = '<!-- END NEW PROPERTIES -->'
HEADER_PROPOSALS = '<!-- NEW PROPOSALS DO NOT REMOVE -->'
FOOTER_PROPOSALS = '<!-- END NEW PROPOSALS -->'


def get_latest_newsletter() -> str:
    cat = pwb.Category(SITE, 'Wikidata status updates')

    for page in cat.articles(namespaces=4, sortby='timestamp', reverse=True):
        if not 'Wikidata:Status updates/2' in page.title():
            continue

        if page.depth != 1:
            continue

        return str(page.oldest_revision['timestamp'])

    raise RuntimeError('No latest newsletter found')


def is_external_id_proposal(page:pwb.Page) -> bool:
    dtype_strings = [ 'external-id' , 'id', 'externalidentifier' ]

    text = re.sub(r'(<!([^>]+)>)|\s|\n', '', page.get()).lower()

    for dtype_str in dtype_strings:
        if text.count(f'datatype={dtype_str}') > 0:
            return True

    return False  # if indeterminable, assume not external_id


def is_proposal_open_or_ready(page:pwb.Page) -> bool:
    text = re.sub(r'(<!([^>]+)>)|\s|\n', '', page.get()).lower()

    if text.count('status=|') > 0:
        return True

    if text.count('status=ready|') > 0:
        return True

    return False


def get_proposal_description(page:pwb.Page) -> str:
    wikitext = mwparserfromhell.parse(page.text)
    templates = wikitext.filter_templates(recursive=False)

    for template in templates:
        if template.name.strip() != 'Property proposal':
            continue

        if not template.has('description'):
            continue

        description = template.get('description').value

        sub_templates = description.filter_templates()
        for sub_template in sub_templates:
            if sub_template.name.strip() != 'TranslateThis':
                continue

            if not sub_template.has('en'):
                continue

            pattern = re.compile(r'<!--.*?-->')
            description = re.sub(
                pattern,
                '',
                str(sub_template.get('en').value)
            ).strip()

            return description

        else:
            return str(description).strip()  # raw description

    return "''(no English description proposed yet)''"


def new_proposals(startdate:str) -> str:
    ext_id_proposals:list[str] = []
    general_proposals:list[str] = []

    cat = pwb.Category(SITE, 'Open property proposals')

    for page in cat.articles(recurse=1, namespaces=4, sortby='timestamp', starttime=startdate):
        if not is_proposal_open_or_ready(page):
            continue

        str_to_append = f'[[:d:{page.title()}|{page.title().replace("Wikidata:Property proposal/", "")}]]'

        if is_external_id_proposal(page):
            str_to_append = f'[[:d:{page.title()}|{page.title().replace("Wikidata:Property proposal/", "")}]]'
            ext_id_proposals.append(str_to_append)
        else:
            str_to_append = f"""***[[:d:{page.title()}|{page.title().replace("Wikidata:Property proposal/", "")}]] (<nowiki>{get_proposal_description(page)}</nowiki>)"""
            general_proposals.append(str_to_append)

    ext_id_text = ', '.join(ext_id_proposals) if len(ext_id_proposals) else 'none'
    general_text = '\n' + '\n'.join(general_proposals) if len(general_proposals) else 'none'

    text = f"""* New [[d:Special:MyLanguage/Wikidata:Property proposal|property proposals]] to review:
** General datatypes: {general_text}
** External identifiers: {ext_id_text}"""

    return text


def new_properties(startdate:str) -> str:
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rctype': 'new',
        'rcnamespace': '120',
        'rclimit': '100',
        'rcend': startdate,
        'format': 'json'
    }
    response = requests.get(
        'https://www.wikidata.org/w/api.php',
        params=params
    )
    payload = response.json()
    payload.get('query', {}).get('recentchanges', []).sort(key=lambda revision: revision.get('pageid', 0))

    ext_id_properties:list[str] = []
    general_properties:list[str] = []

    for revision in payload.get('query', {}).get('recentchanges', []):
        pid = revision.get('title', '').replace('Property:', '')

        entity = pwb.PropertyPage(REPO, pid)
        entity.get()

        en_label = entity.labels.get('en', pid)

        if entity.type == 'external-id':
            str_to_append = f'[[:d:{revision.get("title", "")}|{en_label}]]'
            ext_id_properties.append(str_to_append)
        else:
            en_description = entity.descriptions.get('en', "''(without English description)''")
            str_to_append = f"""***[[:d:{revision.get("title", "")}|{en_label}]] (<nowiki>{en_description}</nowiki>)"""
            general_properties.append(str_to_append)

    ext_id_text = ', '.join(ext_id_properties) if ext_id_properties else 'none'
    general_text = '\n' + '\n'.join(general_properties) if general_properties else 'none'

    text = f"""* Newest [[d:Special:ListProperties|properties]]:
** General datatypes: {general_text}
** External identifiers: {ext_id_text}"""

    return text


def main() -> None:
    latest_newsletter = get_latest_newsletter()
    startdate = f'{latest_newsletter[:11]}00:00:00Z'

    text_new_properties = new_properties(startdate)
    text_new_proposals = new_proposals(startdate)

    page = pwb.Page(SITE, 'Wikidata:Status updates/Next')

    new_text = re.sub(
        HEADER_PROPERTIES + '.*' + FOOTER_PROPERTIES,
        HEADER_PROPERTIES + '\n' + text_new_properties + '\n' + FOOTER_PROPERTIES,
        page.get(),
        flags=re.DOTALL
    )
    new_text = re.sub(
        HEADER_PROPOSALS + '.*' + FOOTER_PROPOSALS,
        HEADER_PROPOSALS + '\n' + text_new_proposals + '\n' + FOOTER_PROPOSALS,
        new_text,
        flags=re.DOTALL
    )

    page.text = new_text
    page.save(summary='Bot: Updating list of new properties and property proposals')


if __name__ == '__main__':
    main()
