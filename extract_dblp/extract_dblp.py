#!/usr/bin/env python3
"""
Extract author-to-publication data from dblp.xml for ICSA, ICSE, and ECSA since 2015.

Output: author_publications.csv
  author     - author name as it appears in DBLP
  pub_key    - DBLP record key (e.g. conf/icse/Smith2020)
  title      - paper title
  year       - publication year
  conference - ICSA | ICSE | ECSA

Requires: pip install lxml
"""

import csv
import os
import shutil
from lxml import etree

XML_PATH  = 'dblp.xml/dblp.xml'
DTD_SRC   = 'dblp.dtd'
DTD_DST   = 'dblp.xml/dblp.dtd'   # must be co-located with the XML for entity resolution
OUTPUT    = 'author_publications.csv'

TARGET_CONFERENCES = {'icsa', 'icse', 'ecsa'}
MIN_YEAR = 2015


def get_text(elem, tag):
    child = elem.find(tag)
    if child is None:
        return ''
    return ''.join(child.itertext()).strip()


def main():
    # DTD must live next to the XML so lxml can resolve SYSTEM "dblp.dtd"
    if not os.path.exists(DTD_DST):
        if os.path.exists(DTD_SRC):
            shutil.copy(DTD_SRC, DTD_DST)
            print(f"Copied {DTD_SRC} -> {DTD_DST}")
        else:
            print(f"Warning: {DTD_SRC} not found; entity resolution may fail.")

    print(f"Streaming {XML_PATH} (~4 GB, may take several minutes)...")

    rows = []
    pub_count = 0

    context = etree.iterparse(
        XML_PATH,
        events=('end',),
        tag='inproceedings',
        load_dtd=True,
        resolve_entities=True,
        no_network=True,
        recover=True,
    )

    for _, elem in context:
        key = elem.get('key', '')
        parts = key.split('/')

        # DBLP keys for conference papers follow: conf/<conf-id>/...
        if len(parts) >= 2 and parts[0] == 'conf' and parts[1] in TARGET_CONFERENCES:
            try:
                year = int(get_text(elem, 'year'))
            except (ValueError, TypeError):
                elem.clear()
                continue

            if year >= MIN_YEAR:
                title      = get_text(elem, 'title')
                conference = parts[1].upper()

                for author_elem in elem.findall('author'):
                    author = ''.join(author_elem.itertext()).strip()
                    if author:
                        rows.append((author, key, title, year, conference))

                pub_count += 1
                if pub_count % 500 == 0:
                    print(f"  {pub_count} matching publications...", end='\r', flush=True)

        # Free memory as we go — critical for a 4 GB file
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    print(f"\nFound {pub_count} publications ({len(rows)} author-publication pairs).")
    print(f"Writing {OUTPUT}...")

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'pub_key', 'title', 'year', 'conference'])
        writer.writerows(rows)

    print("Done.")


if __name__ == '__main__':
    main()