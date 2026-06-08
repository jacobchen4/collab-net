"""
Pulls the coauthorship graph from Neo4j Aura and saves two networkx graphs:
  analysis/multigraph.pkl  - MultiGraph (one edge per shared paper)
  analysis/graph.pkl       - Graph (collapsed; weight = # shared papers, distance = 1/weight)

Run from the repo root:
  python analysis/fetch_graph.py
"""

import pickle
import sys
from collections import defaultdict

import networkx as nx
import pandas as pd

sys.path.insert(0, ".")
from analysis.connection import session


def fetch_graph():
    with session() as s:
        print("Fetching authors...")
        author_rows = s.run(
            "MATCH (a:author) RETURN elementId(a) AS aid, a.author AS aname"
        ).data()
        print(f"  {len(author_rows):,} authors")

        print("Fetching COAUTHORED_WITH edges...")
        edge_rows = s.run(
            """
            MATCH (a:author)-[c:COAUTHORED_WITH]->(b:author)
            RETURN elementId(a) AS aid, elementId(b) AS bid, c.pub_key AS pub_key
            """
        ).data()
        print(f"  {len(edge_rows):,} directed COAUTHORED_WITH records")

    # --- MultiGraph (raw, one edge per paper) ---
    MG = nx.MultiGraph()
    for row in author_rows:
        MG.add_node(row["aid"], name=row["aname"])
    for row in edge_rows:
        MG.add_edge(row["aid"], row["bid"], pub_key=row["pub_key"])

    # --- Collapsed weighted Graph ---
    # Count edges between each pair
    pair_counts = defaultdict(int)
    for row in edge_rows:
        key = (min(row["aid"], row["bid"]), max(row["aid"], row["bid"]))
        pair_counts[key] += 1

    G = nx.Graph()
    for row in author_rows:
        G.add_node(row["aid"], name=row["aname"])
    for (u, v), count in pair_counts.items():
        G.add_edge(u, v, weight=count, distance=1.0 / count)

    print(f"\nMultiGraph  — nodes: {MG.number_of_nodes():,}, edges: {MG.number_of_edges():,}")
    print(f"Weighted Graph — nodes: {G.number_of_nodes():,}, edges: {G.number_of_edges():,}")

    with open("analysis/multigraph.pkl", "wb") as f:
        pickle.dump(MG, f)
    with open("analysis/graph.pkl", "wb") as f:
        pickle.dump(G, f)

    print("\nSaved: analysis/multigraph.pkl, analysis/graph.pkl")


def build_graphs_from_subgraph_df(df: pd.DataFrame):
    """
    Build MG and G from a DataFrame returned by database_load.getSubgraph.
    Expected columns: authors, edges (pub_key on COAUTHORED_WITH), coauthors.

    The subgraph query traverses undirected edges so each pair appears twice;
    this function deduplicates before constructing the graphs.
    """
    author_names = set(df["authors"].tolist() + df["coauthors"].tolist())

    MG = nx.MultiGraph()
    for name in author_names:
        MG.add_node(name, name=name)

    # Normalise each (a, b, pub_key) so duplicates from undirected traversal are dropped
    seen: set = set()
    for _, row in df.iterrows():
        a, b, pub_key = row["authors"], row["coauthors"], row["edges"]
        key = (min(a, b), max(a, b), pub_key)
        if key not in seen:
            seen.add(key)
            MG.add_edge(a, b, pub_key=pub_key)

    pair_counts: dict = defaultdict(int)
    for a, b, _ in seen:
        pair_counts[(a, b)] += 1

    G = nx.Graph()
    for name in author_names:
        G.add_node(name, name=name)
    for (u, v), count in pair_counts.items():
        G.add_edge(u, v, weight=count, distance=1.0 / count)

    return MG, G


def save_graphs(MG, G, mg_path: str, g_path: str):
    """Pickle MG and G to the given paths."""
    with open(mg_path, "wb") as f:
        pickle.dump(MG, f)
    with open(g_path, "wb") as f:
        pickle.dump(G, f)


if __name__ == "__main__":
    fetch_graph()
