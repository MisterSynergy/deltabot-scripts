#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import re
from time import sleep
from typing import Any

import pywikibot as pwb
from pywikibot.data import api
from pywikibot.exceptions import IsNotRedirectPageError


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()


def get_token() -> str:
    params = {
        'action' : 'query',
        'meta' : 'tokens',
    }
    request = api.Request(SITE, parameters=params)
    data = request.submit()

    token = data.get('query', {}).get('tokens', {}).get('csrftoken')
    if token is None:
        raise RuntimeError('No valid token obtained')

    return token


def redirect(from_id:str, to_id:str) -> None:
    token = get_token()

    params = {
        'action' : 'wbcreateredirect',
        'from' : from_id,
        'to' : to_id,
        'bot' : '1',
        'token' : token,
    }
    request = api.Request(SITE, parameters=params)
    _ = request.submit()


def get_double_redirects() -> list[dict[str, Any]]:
    #https://www.wikidata.org/w/api.php?action=query&list=querypage&qppage=DoubleRedirects&qplimit=500
    params = {
        'action' : 'query',
        'list' : 'querypage',
        'qppage' : 'DoubleRedirects',
        'qplimit' : '500',
    }
    request = api.Request(SITE, parameters=params)
    data = request.submit()

    return data.get('query', {}).get('querypage', {}).get('results', [])


def main() -> None:
    for row in get_double_redirects():
        ns = row.get('ns')
        page_title = row.get('title')
        if ns is None or page_title is None:
            continue

        if ns not in [ 0, 146 ]:
            continue

        if ns == 0 and re.match(r'^Q[\d]+$', page_title) is not None:
            entity = pwb.ItemPage(REPO, page_title)
            try:
                target_qid = entity.getRedirectTarget().getRedirectTarget().getID()
            except IsNotRedirectPageError as exception:
                continue
            else:
                redirect(page_title, target_qid)

        elif ns == 146 and re.match(r'^Lexeme:L[\d]+$', page_title) is not None:
            entity = pwb.LexemePage(REPO, page_title)
            try:
                target_lid = entity.getRedirectTarget().getRedirectTarget().title()
            except IsNotRedirectPageError as exception:
                continue
            else:
                redirect(page_title.replace('Lexeme:', ''), target_lid.replace('Lexeme:', ''))


if __name__=='__main__':
    main()
