"""Filter out the disambiguation pairs that were NOT substituted, so they can
be reviewed manually.

A pair gets auto-substituted only when n_shared_coauthors > 0 (see
apply_disambiguation.py). Everything else (n_shared_coauthors == 0) is left
untouched -- those are the suspected-duplicate names that still need a human to
decide whether they're the same person.
"""
import csv

DISAMB = "disambiguation_strict.csv"
OUT = "disambiguation_unresolved.csv"

with open(DISAMB, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

substituted = [r for r in rows if int(r["n_shared_coauthors"]) > 0]
unresolved = [r for r in rows if int(r["n_shared_coauthors"]) == 0]

with open(OUT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unresolved)

print(f"Total suspected-duplicate pairs : {len(rows)}")
print(f"  substituted (shared > 0)      : {len(substituted)}")
print(f"  NOT substituted (shared == 0) : {len(unresolved)}  -> written to {OUT}")
print()
print("Preview of pairs left for manual review:")
for r in unresolved[:15]:
    print(f"  {r['name_a']!r}  <->  {r['name_b']!r}   (fuzzy={r['fuzzy_ratio']})")
