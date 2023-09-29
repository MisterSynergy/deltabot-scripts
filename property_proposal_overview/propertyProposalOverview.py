#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import datetime
import re

today = datetime.today()

site = pywikibot.Site('wikidata','wikidata')
 
def createOverview(proposals):
    proposals = [value for key, value in list(proposals.items())]   
    proposals.sort(key=lambda x:x['age'])    
    
    text = u'open proposals: '+str(len(proposals))+'\n\n== All open property proposals ==\n{| class="wikitable sortable"\n|-\n!Proposal !! Category !! Days open || Days since last edit\n'
    for proposal in proposals:
        if proposal['age'] < 7:
            style = ''
        elif proposal['age'] < 14:
            style = u'style="background-color:#F8E0E0"'
        elif proposal['age'] < 31:
            style = u'style="background-color:#F6CECE"'
        else:
            style = u'style="background-color:#F5A9A9"'
        text += u'|- {0}\n|[[Wikidata:Property_proposal/{1}|{1}]] || {2} || {3} || {4}\n'.format(style, proposal['name'], ', '.join(proposal['category']), proposal['age'], proposal['lastedit'])
    text += u'|}\n[[Category:Property proposals|Overview]]'
    page = pywikibot.Page(site, 'Wikidata:Property_proposal/Overview')
    page.put(text, summary='upd', minorEdit=False)

def main():
    all = {}
    categories = ['Generic', 'Place', 'Authority control', 'Creative work', 'Transportation', 'Person', 'Natural science', 'Organization', 'Sister projects', 'Sports', 'Lexemes', 'Computing']
    for category in categories:
        try:
            page = pywikibot.Page(site, 'Wikidata:Property_proposal/'+category)
            fo = page.get().split('</noinclude>')
            proposals = re.findall('{{Wikidata:Property proposal/(.*?)}}', fo[1].replace('_',' '))
            for proposal in proposals:
                page2 = pywikibot.Page(site, 'Wikidata:Property proposal/'+proposal)
                if page2.isRedirectPage():
                    page2 = page2.getRedirectTarget()
                    proposal = page2.title()[27:]
                if not page2.exists():
                    continue
                text = re.sub(r'(<!([^>]+)>)|\s|\n', '', page2.get())
                if text.count('status=|') or text.count('status=ready|') > 0:
                    history = [rev for rev in page2.revisions()]
                    if proposal not in all:
                        data = {
                            'name': proposal,
                            'category': [category],
                            'age': (today - history[-1].timestamp).days,
                            'lastedit': (today - history[0].timestamp).days
                        }
                        all[proposal] = data
                    else:
                        all[proposal]['category'].append(category)
        except:
            print('error with proposal page '+category)
    createOverview(all)

if __name__ == "__main__":
    main()
