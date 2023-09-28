#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import time
import re

site1 = pywikibot.Site("wikidata", "wikidata")
repo1 = site1.data_repository()
site2 = pywikibot.Site("commons", "commons")
repo2 = site2.data_repository()

CLEANR = re.compile("<.*?>")


def addImage(image):
    print(image)
    target = pywikibot.FilePage(repo2, image)
    item = pywikibot.ItemPage(repo1, "Q14334596")
    item.get()
    if "P18" in item.claims:
        if len(item.claims["P18"]) == 1:
            item.claims["P18"][0].changeTarget(target)
            return True
    claim = pywikibot.Claim(repo1, "P18")
    claim.setTarget(target)
    item.addClaim(claim)
    return True


page = pywikibot.Page(site2, "Template:Potd/" + time.strftime("%Y-%m-%d"))
cont = page.get().replace("\n", "")
cleantext = re.sub(CLEANR, "", cont)
res = re.search("\{\{Potd filename\|(.*?)\|", cleantext)
if res:
    file_name = res.group(1).replace("_", " ")
    if "1=" in file_name:
        file_name = file_name.replace("1=", "")
    addImage(file_name.strip())
