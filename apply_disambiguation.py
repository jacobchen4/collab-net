"""Substitute name_b -> name_a in author_publications.csv for the first 200
disambiguation pairs that share more than 2 co-authors."""
import csv

DISAMB = "disambiguation_strict.csv"
PUBS = "author_publications.csv"

# 1. Collect qualifying pairs (n_shared_coauthors > 0), entire file, in order.
pairs = []
with open(DISAMB, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if int(r["n_shared_coauthors"]) > 0:
            pairs.append((r["name_b"], r["name_a"]))

# 2. Build name_b -> name_a map (first occurrence of a name_b wins).
raw = {}
for b, a in pairs:
    if b not in raw:
        raw[b] = a

# 3. Resolve transitively (a name_a may itself be a name_b elsewhere),
#    with cycle protection.
def resolve(name):
    seen = set()
    while name in raw and name not in seen:
        seen.add(name)
        name = raw[name]
    return name

mapping = {b: resolve(b) for b in raw}
# Drop no-op entries.
mapping = {b: a for b, a in mapping.items() if b != a}

# 4. Apply to the author column of author_publications.csv.
with open(PUBS, encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

author_idx = header.index("author")
counts = {b: 0 for b in mapping}
for row in rows:
    name = row[author_idx]
    if name in mapping:
        row[author_idx] = mapping[name]
        counts[name] += 1

with open(PUBS, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

# 5. Report.
total = sum(counts.values())
print(f"Applied {len(mapping)} name substitutions; {total} author rows updated.\n")
for b, a in mapping.items():
    print(f"  {counts[b]:4d}  {b!r} -> {a!r}")
