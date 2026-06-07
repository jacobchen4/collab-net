"""
Identifies authors who published across multiple conferences (ICSA, ICSE, ECSA)
and cross-references their network metrics from author_metrics.csv.

Outputs: analysis/bridge_authors.csv
  - One row per author who published in 2+ conferences
  - Includes which conferences, publication counts per conference, and key metrics

Run from the repo root:
  python analysis/bridge_authors.py
"""

import pandas as pd


def main():
    pubs = pd.read_csv("csvs/author_publications.csv")
    metrics = pd.read_csv("analysis/author_metrics.csv")

    # Count publications per author per conference
    conf_counts = (
        pubs.groupby(["author", "conference"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    conferences = [c for c in ["ICSA", "ICSE", "ECSA"] if c in conf_counts.columns]
    for c in conferences:
        if c not in conf_counts.columns:
            conf_counts[c] = 0

    conf_counts["n_conferences"] = (conf_counts[conferences] > 0).sum(axis=1)
    conf_counts["total_pubs"] = conf_counts[conferences].sum(axis=1)

    bridges = conf_counts[conf_counts["n_conferences"] >= 2].copy()

    bridges = bridges.merge(
        metrics[["name", "database_id", "degree_weighted", "betweenness_unweighted",
                 "betweenness_weighted", "clustering_unweighted", "connected_component"]],
        left_on="author",
        right_on="name",
        how="left"
    ).drop(columns="name")

    bridges = bridges.rename(columns={"author": "name"})
    bridges = bridges.sort_values(["n_conferences", "betweenness_unweighted"], ascending=[False, False])

    col_order = ["name", "database_id", "n_conferences"] + conferences + \
                ["total_pubs", "degree_weighted", "betweenness_unweighted",
                 "betweenness_weighted", "clustering_unweighted", "connected_component"]
    bridges = bridges[[c for c in col_order if c in bridges.columns]]

    bridges.to_csv("analysis/bridge_authors.csv", index=False)

    print(f"Authors publishing in 2+ conferences: {len(bridges):,}")
    print(f"Authors publishing in all 3 conferences: {(bridges['n_conferences'] == 3).sum():,}")
    print(f"\nConference overlap breakdown:")
    print(bridges["n_conferences"].value_counts().sort_index().to_string())
    print(f"\nWrote {len(bridges):,} rows to analysis/bridge_authors.csv")


if __name__ == "__main__":
    main()
