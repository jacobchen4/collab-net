import csv

STRICT_PATH = "csvs/disambiguation_strict.csv"
UNRESOLVED_PATH = "csvs/disambiguation_unresolved.csv"
MANUAL_PATH = "csvs/disambiguation_manual.csv"
OUTPUT_PATH = "csvs/disambiguation_comparison.csv"


def load_pairs(path, skip_blank_lines=False):
    pairs = {}
    with open(path, newline="", encoding="utf-8") as f:
        if skip_blank_lines:
            lines = [line for line in f if line.strip()]
            reader = csv.DictReader(lines)
        else:
            reader = csv.DictReader(f)
        for row in reader:
            key = (row["name_a"].strip(), row["name_b"].strip())
            pairs[key] = row
    return pairs


strict = load_pairs(STRICT_PATH)
unresolved = load_pairs(UNRESOLVED_PATH)
manual = load_pairs(MANUAL_PATH, skip_blank_lines=True)

resolved = {k: v for k, v in strict.items() if k not in unresolved}

all_keys = sorted(set(resolved) | set(manual))

with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "name_a", "name_b", "canonical_a", "canonical_b",
        "fuzzy_ratio", "n_shared_coauthors", "status"
    ])
    for key in all_keys:
        in_resolved = key in resolved
        in_manual = key in manual
        row = resolved.get(key) or manual.get(key)

        if in_resolved and in_manual:
            status = "both"
        elif in_resolved:
            status = "resolved_only"
        else:
            status = "manual_only"

        writer.writerow([
            row["name_a"], row["name_b"],
            row["canonical_a"], row["canonical_b"],
            row["fuzzy_ratio"], row["n_shared_coauthors"],
            status
        ])

# Print summary
from collections import Counter
counts = Counter()
for key in all_keys:
    in_r = key in resolved
    in_m = key in manual
    if in_r and in_m:
        counts["both"] += 1
    elif in_r:
        counts["resolved_only"] += 1
    else:
        counts["manual_only"] += 1

print(f"Written to {OUTPUT_PATH}\n")
print(f"  both:           {counts['both']}")
print(f"  resolved_only:  {counts['resolved_only']}")
print(f"  manual_only:    {counts['manual_only']}")
print(f"  total:          {sum(counts.values())}")
