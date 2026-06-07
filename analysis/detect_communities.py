"""
Runs Louvain community detection on the weighted coauthorship graph and
assigns each author to a research community.

Community IDs are assigned in descending order by size (0 = largest community).

Outputs: analysis/author_communities.csv

Run from the repo root:
  python analysis/detect_communities.py
"""

import pickle
import networkx as nx
import pandas as pd


def main():
    print("Loading graph...")
    with open("analysis/graph.pkl", "rb") as f:
        G = pickle.load(f)

    print("Running Louvain community detection...")
    communities = nx.community.louvain_communities(G, weight="weight", seed=42)
    communities = sorted(communities, key=len, reverse=True)
    print(f"  Found {len(communities):,} communities")
    print(f"  Largest: {len(communities[0]):,} authors")
    print(f"  Smallest: {len(communities[-1]):,} authors")

    node_to_community = {}
    for idx, community in enumerate(communities):
        for node in community:
            node_to_community[node] = idx

    community_sizes = {idx: len(c) for idx, c in enumerate(communities)}

    rows = []
    for node_id, data in G.nodes(data=True):
        cid = node_to_community[node_id]
        rows.append({
            "name": data["name"],
            "database_id": node_id,
            "community_id": cid,
            "community_size": community_sizes[cid],
        })

    df = pd.DataFrame(rows).sort_values(["community_id", "name"])
    df.to_csv("analysis/author_communities.csv", index=False)
    print(f"\nWrote {len(df):,} rows to analysis/author_communities.csv")

    print("\nTop 10 communities by size:")
    top = df.drop_duplicates("community_id").nsmallest(10, "community_id")[["community_id", "community_size"]]
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
