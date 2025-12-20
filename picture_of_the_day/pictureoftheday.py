#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import re
from time import strftime

import pywikibot as pwb


SITE_WD = pwb.Site('wikidata', 'wikidata')
REPO_WD = SITE_WD.data_repository()

SITE_COMMONS = pwb.Site('commons', 'commons')
REPO_COMMONS = SITE_COMMONS.data_repository()

POTD_TEMPLATE_QID = 'Q14334596'  # item for Template:POTD
IMAGE_PID = 'P18'

CLEANR = re.compile(r"<.*?>")


def add_image(image:str) -> None:
    print(image)

    target_image = pwb.FilePage(REPO_COMMONS, image)
    item = pwb.ItemPage(REPO_WD, POTD_TEMPLATE_QID)
    item.get()

    if IMAGE_PID not in item.claims:
        claim = pwb.Claim(REPO_WD, IMAGE_PID)
        claim.setTarget(target_image)
        item.addClaim(claim)
        return

    if len(item.claims[IMAGE_PID])==1:
        item.claims[IMAGE_PID][0].changeTarget(target_image)
        return

    # if there are more than one P18 claims on that item, nothing happens.


def main() -> None:
    page = pwb.Page(SITE_COMMONS, f'Template:Potd/{strftime("%Y-%m-%d")}')
    page_content = page.get().replace('\n', '')
    clean_text = re.sub(CLEANR, '', page_content)

    res = re.search(r'\{\{Potd filename\|(.*?)\|', clean_text)
    if res:
        file_name = res.group(1).replace('_', ' ')

        if '1=' in file_name:
            file_name = file_name.replace('1=', '')

        add_image(file_name.strip())


if __name__=='__main__':
    main()
