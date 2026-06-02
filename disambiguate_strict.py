#!/usr/bin/env python3
"""
Strict author disambiguation: diacritic normalization + middle name removal.

Finds pairs of distinct author strings that likely refer to the same person
after (1) folding diacritics/special characters and (2) dropping middle
names/initials, leaving only first + last.

Output: top 200 pairs ranked by fuzzy ratio, with shared co-authors.
  disambiguation_strict.csv
"""

import csv
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

INPUT  = 'author_publications.csv'
OUTPUT = 'disambiguation_strict.csv'

FUZZY_THRESHOLD = 0.80  # on the canonical (first+last, diacritic-folded) form
TOP_N = 500


# ── name normalisation ────────────────────────────────────────────────────────

def strip_dblp_suffix(name: str) -> str:
    return re.sub(r'\s+\d{4}$', '', name).strip()


def fold_diacritics(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


def canonical(name: str) -> str:
    """
    Diacritic-fold, strip DBLP suffix, lowercase, then keep only the
    first and last whitespace-separated tokens (drop all middle names/initials).
    """
    base = fold_diacritics(strip_dblp_suffix(name)).lower()
    parts = base.split()
    if len(parts) <= 2:
        return base
    return f"{parts[0]} {parts[-1]}"


def last_token(name: str) -> str:
    parts = canonical(name).split()
    return parts[-1] if parts else ''


# ── data loading ──────────────────────────────────────────────────────────────

def load(path: str):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append(row)

    coauthors_by_pub = defaultdict(set)
    for row in rows:
        coauthors_by_pub[row['pub_key']].add(strip_dblp_suffix(row['author']))

    pubs_by_author = defaultdict(list)
    for row in rows:
        pubs_by_author[row['author']].append(row)

    return coauthors_by_pub, pubs_by_author


# ── matching ──────────────────────────────────────────────────────────────────

def compare_pairs(pubs_by_author: dict, coauthors_by_pub: dict) -> list:
    # Block by canonical last name to avoid O(n^2) over all 14k authors
    by_last: dict = defaultdict(list)
    for author in pubs_by_author:
        by_last[last_token(author)].append(author)

    findings = []

    for group in by_last.values():
        if len(group) < 2:
            continue
        group = sorted(group)
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                # Skip DBLP-disambiguated variants of the same base name
                if strip_dblp_suffix(a) == strip_dblp_suffix(b):
                    continue

                ca, cb = canonical(a), canonical(b)
                # Skip if canonical forms are identical raw strings
                # (already the same person or a trivial normalisation match)
                ratio = SequenceMatcher(None, ca, cb).ratio()
                if ratio < FUZZY_THRESHOLD:
                    continue

                # Shared co-authors
                all_ca = set()
                for r in pubs_by_author[a]:
                    all_ca |= coauthors_by_pub[r['pub_key']]
                all_ca.discard(strip_dblp_suffix(a))

                all_cb = set()
                for r in pubs_by_author[b]:
                    all_cb |= coauthors_by_pub[r['pub_key']]
                all_cb.discard(strip_dblp_suffix(b))

                shared = sorted(all_ca & all_cb)

                findings.append({
                    'name_a':          a,
                    'name_b':          b,
                    'canonical_a':     ca,
                    'canonical_b':     cb,
                    'fuzzy_ratio':     round(ratio, 3),
                    'n_shared_coauthors': len(shared),
                    'shared_coauthors': '; '.join(shared),
                })

    findings.sort(key=lambda x: (-x['fuzzy_ratio'], -x['n_shared_coauthors']))
    return findings[:TOP_N]


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    coauthors_by_pub, pubs_by_author = load(INPUT)
    print(f"  {len(pubs_by_author)} unique author strings")

    print("Comparing pairs...")
    results = compare_pairs(pubs_by_author, coauthors_by_pub)

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'name_a', 'name_b', 'canonical_a', 'canonical_b',
            'fuzzy_ratio', 'n_shared_coauthors', 'shared_coauthors',
        ])
        w.writeheader()
        w.writerows(results)

    print(f"  Written {len(results)} rows -> {OUTPUT}")
    print()

    # Console preview
    print(f"{'name_a':<40} {'name_b':<40} {'ratio':>6}  {'shared':>6}  shared_coauthors")
    print('-' * 120)
    for r in results:
        shared_preview = (r['shared_coauthors'][:60] + '...') if len(r['shared_coauthors']) > 60 else r['shared_coauthors']
        print(f"{r['name_a']:<40} {r['name_b']:<40} {r['fuzzy_ratio']:>6.3f}  {r['n_shared_coauthors']:>6}  {shared_preview}")


if __name__ == '__main__':
    main()
