#!/usr/bin/env python3
"""
Extract author ORCIDs for ICSA, ICSE, and ECSA papers (>=2015) from dblp.xml.

Output
------
author_orcids.csv   One row per unique (author, orcid) pair.
                    Columns: author, orcid, pub_keys, n_pubs

pub_keys is a semicolon-separated list of every pub_key where that ORCID
was observed, enabling joins back to author_publications.csv.

Requires: pip install lxml
"""

import csv
import os
import shutil
from collections import defaultdict
from lxml import etree

XML_PATH = 'dblp.xml/dblp.xml'
DTD_SRC  = 'dblp.dtd'
DTD_DST  = 'dblp.xml/dblp.dtd'
OUTPUT   = 'author_orcids.csv'

TARGET_CONFERENCES = {'icsa', 'icse', 'ecsa'}
MIN_YEAR = 2015


def get_text(elem, tag):
    child = elem.find(tag)
    if child is None:
        return ''
    return ''.join(child.itertext()).strip()


def main():
    if not os.path.exists(DTD_DST):
        if os.path.exists(DTD_SRC):
            shutil.copy(DTD_SRC, DTD_DST)
            print(f"Copied {DTD_SRC} -> {DTD_DST}")
        else:
            print(f"Warning: {DTD_SRC} not found; entity resolution may fail.")

    print(f"Streaming {XML_PATH} (~4 GB, may take several minutes)...")

    # (author_name, orcid) -> list of pub_keys
    orcid_map = defaultdict(list)
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

        if not (len(parts) >= 2 and parts[0] == 'conf' and parts[1] in TARGET_CONFERENCES):
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        try:
            year = int(get_text(elem, 'year'))
        except (ValueError, TypeError):
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        if year < MIN_YEAR:
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        pub_count += 1

        for author_elem in elem.findall('author'):
            orcid = author_elem.get('orcid', '').strip()
            if not orcid:
                continue
            author = ''.join(author_elem.itertext()).strip()
            if author:
                orcid_map[(author, orcid)].append(key)

        if pub_count % 500 == 0:
            print(f"  {pub_count} matching publications...", end='\r', flush=True)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    print(f"\nFound {pub_count} publications, {len(orcid_map)} unique (author, orcid) pairs.")
    print(f"Writing {OUTPUT}...")

    rows = sorted(
        [
            (author, orcid, '; '.join(pub_keys), len(pub_keys))
            for (author, orcid), pub_keys in orcid_map.items()
        ],
        key=lambda r: r[0].lower(),
    )

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['author', 'orcid', 'pub_keys', 'n_pubs'])
        w.writerows(rows)

    print("Done.")


if __name__ == '__main__':
    main()
