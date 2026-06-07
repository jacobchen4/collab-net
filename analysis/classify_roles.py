"""
Classifies each author into a structural network role based on their
betweenness, degree, and clustering metrics in author_metrics.csv.

Roles (priority order):
  broker     - high betweenness, low clustering (bridges disconnected groups)
  hub        - high degree, low clustering (many collaborators, loosely connected)
  embedded   - high clustering, low betweenness (tight local clique)
  peripheral - low degree (few connections overall)
  core       - well-connected but not extreme on any single dimension

Outputs: analysis/author_roles.csv

Run from the repo root:
  python analysis/classify_roles.py
"""

import pandas as pd


HIGH = 75  # percentile threshold for "high"
LOW  = 25  # percentile threshold for "low"


def classify(row, thresholds):
    b_high = row["betweenness_unweighted"] >= thresholds["betweenness_high"]
    b_low  = row["betweenness_unweighted"] <  thresholds["betweenness_low"]
    d_high = row["degree_weighted"]        >= thresholds["degree_high"]
    d_low  = row["degree_weighted"]        <  thresholds["degree_low"]
    c_high = row["clustering_unweighted"]  >= thresholds["clustering_high"]
    c_low  = row["clustering_unweighted"]  <  thresholds["clustering_low"]

    if b_high and c_low:
        return "broker"
    if d_high and c_low:
        return "hub"
    if c_high and b_low:
        return "embedded"
    if d_low:
        return "peripheral"
    return "core"


def main():
    df = pd.read_csv("analysis/author_metrics.csv")

    thresholds = {
        "betweenness_high": df["betweenness_unweighted"].quantile(HIGH / 100),
        "betweenness_low":  df["betweenness_unweighted"].quantile(LOW  / 100),
        "degree_high":      df["degree_weighted"].quantile(HIGH / 100),
        "degree_low":       df["degree_weighted"].quantile(LOW  / 100),
        "clustering_high":  df["clustering_unweighted"].quantile(HIGH / 100),
        "clustering_low":   df["clustering_unweighted"].quantile(LOW  / 100),
    }

    df["role"] = df.apply(classify, axis=1, thresholds=thresholds)

    out = df[["name", "database_id", "degree_weighted", "degree_total",
              "betweenness_unweighted", "betweenness_weighted",
              "clustering_unweighted", "clustering_weighted",
              "connected_component", "role"]]

    out.to_csv("analysis/author_roles.csv", index=False)

    print("Role distribution:")
    print(df["role"].value_counts().to_string())
    print(f"\nWrote {len(out):,} rows to analysis/author_roles.csv")


if __name__ == "__main__":
    main()
