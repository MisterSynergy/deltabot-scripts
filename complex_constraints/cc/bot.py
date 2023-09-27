#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot as pwb


SITE = pwb.Site('wikidata', 'wikidata')


def edit_page(page_title:str, text:str, summary:str='upd') -> None:
    page = pwb.Page(SITE, page_title)
    page.text = text
    page.save(summary=summary, minor=False)
