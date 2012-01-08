#!/usr/bin/env python
# -*- coding: utf-8 -*-

import feedparser
from pyquery import PyQuery

url = "http://www.korean-flashcards.com/rss-feed-word.php?level={0:d}"

def get_words(level=1):
    feed = feedparser.parse(url.format(level))
    out = []

    for e in feed.entries:
        pq = PyQuery(e.description)
        kor, pron, trans = pq.find('font')
        link = pq.find('a')[0]
        out.append((
            PyQuery(kor).text(),
            PyQuery(pron).text(),
            PyQuery(trans).text(),
            link.attrib['href'],
        ))

    return out


if __name__ == '__main__':
    from optparse import OptionParser
    usage="usage: %prog [options] number"
    description="Gets <number> of recent RSS entries from" \
                " korean-flashcards.com word of the day." \
                " <number> defaults to 3."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option('-k', '--korean', action='store_true',
                      help="Show Hangeul")
    parser.add_option('-p', '--pronunciation', action='store_true',
                      help="Show pronunciation (korean-flashcards.com style)")
    parser.add_option('-t', '--translation', action='store_true',
                      help="Show translation")
    parser.add_option('-u', '--url', action='store_true',
                      help="Show url to word on korean-flashcards.com")
    parser.add_option('-l', '--level', type='int', default=1,
                      help="Number representing level 1, 2, or 3."
                           " Basic, the default, is 1.")

    (options, args) = parser.parse_args()
    # args will now be a tuple of args in the order they were entered
    # options will be an object with attributes corresponding to the long-name give for the option (second add_option parameter)

    if not (options.korean or options.pronunciation
            or options.translation or options.url):
        parser.error("You must specify at least one of -k, -p, -t, or -u."
                     " See --help for more info.")

    number = 3 if len(args) == 0 else int(args[0])

    words = get_words(options.level)

    for w in words[:number]:
        if options.korean:
            print(w[0])
        if options.pronunciation:
            print(w[1])
        if options.translation:
            print(w[2])
        if options.url:
            print(w[3])

