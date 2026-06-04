#!/usr/bin/env python3
"""
Extract DOIs for ICSA, ICSE, and ECSA papers (>=2015) from dblp.xml.

Outputs
-------
paper_dois.csv      Papers where a doi.org <ee> entry was found.
                    Columns: pub_key, doi, title, year, conference

paper_no_dois.csv   Papers with no doi.org <ee> entry.
                    Columns: pub_key, title, year, conference

Requires: pip install lxml
"""

import csv
import os
import shutil
from lxml import etree

XML_PATH  = 'dblp.xml/dblp.xml'
DTD_SRC   = 'dblp.dtd'
DTD_DST   = 'dblp.xml/dblp.dtd'
OUT_DOIS  = 'paper_dois.csv'
OUT_NODOI = 'paper_no_dois.csv'

TARGET_CONFERENCES = {'icsa', 'icse', 'ecsa'}
MIN_YEAR = 2015
DOI_PREFIX = 'https://doi.org/'


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

    with_doi = []
    no_doi   = []
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

        title      = get_text(elem, 'title')
        conference = parts[1].upper()
        pub_count += 1

        doi = None
        for ee in elem.findall('ee'):
            val = ''.join(ee.itertext()).strip()
            if val.startswith(DOI_PREFIX):
                doi = val[len(DOI_PREFIX):]
                break

        if doi:
            with_doi.append((key, doi, title, year, conference))
        else:
            no_doi.append((key, title, year, conference))

        if pub_count % 500 == 0:
            print(f"  {pub_count} matching publications...", end='\r', flush=True)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    print(f"\nFound {pub_count} publications: {len(with_doi)} with DOI, {len(no_doi)} without.")

    print(f"Writing {OUT_DOIS}...")
    with open(OUT_DOIS, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['pub_key', 'doi', 'title', 'year', 'conference'])
        w.writerows(with_doi)

    print(f"Writing {OUT_NODOI}...")
    with open(OUT_NODOI, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['pub_key', 'title', 'year', 'conference'])
        w.writerows(no_doi)

    print("Done.")


if __name__ == '__main__':
    main()
