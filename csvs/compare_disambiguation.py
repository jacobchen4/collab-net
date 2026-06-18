import csv
import sys

STRICT_PATH = "csvs/disambiguation_strict.csv"
UNRESOLVED_PATH = "csvs/disambiguation_unresolved.csv"
MANUAL_PATH = "csvs/disambiguation_manual.csv"
RESOLVED_PATH = "csvs/disambiguation_resolved.csv"


def load_pairs(path, skip_blank_lines=False):
    """Return a set of (name_a, name_b) tuples and the full rows keyed by that pair."""
    pairs = set()
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        if skip_blank_lines:
            lines = [line for line in f if line.strip()]
            reader = csv.DictReader(lines)
        else:
            reader = csv.DictReader(f)
        for row in reader:
            key = (row["name_a"].strip(), row["name_b"].strip())
            pairs.add(key)
            rows[key] = row
    return pairs, rows


# Step 1: strict - unresolved = resolved
strict_pairs, strict_rows = load_pairs(STRICT_PATH)
unresolved_pairs, _ = load_pairs(UNRESOLVED_PATH)
resolved_pairs = strict_pairs - unresolved_pairs

fieldnames = ["name_a", "name_b", "canonical_a", "canonical_b",
              "fuzzy_ratio", "n_shared_coauthors", "shared_coauthors"]
with open(RESOLVED_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for key in sorted(resolved_pairs):
        writer.writerow(strict_rows[key])

print(f"Strict entries:     {len(strict_pairs)}")
print(f"Unresolved entries: {len(unresolved_pairs)}")
print(f"Resolved entries:   {len(resolved_pairs)}")
print(f"Written to {RESOLVED_PATH}\n")

# Step 2: compare resolved vs manual
manual_pairs, _ = load_pairs(MANUAL_PATH, skip_blank_lines=True)

in_resolved_not_manual = resolved_pairs - manual_pairs
in_manual_not_resolved = manual_pairs - resolved_pairs

print(f"Resolved entries:  {len(resolved_pairs)}")
print(f"Manual entries:    {len(manual_pairs)}")
print(f"Overlap:           {len(resolved_pairs & manual_pairs)}")
print()

if in_resolved_not_manual:
    print(f"--- In resolved but NOT in manual ({len(in_resolved_not_manual)}): ---")
    for a, b in sorted(in_resolved_not_manual):
        print(f"  {a}  |  {b}")
else:
    print("All resolved entries are present in manual.")

print()

if in_manual_not_resolved:
    print(f"--- In manual but NOT in resolved ({len(in_manual_not_resolved)}): ---")
    for a, b in sorted(in_manual_not_resolved):
        print(f"  {a}  |  {b}")
else:
    print("All manual entries are present in resolved.")
