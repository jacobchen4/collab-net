"""
Loads the pickled graphs from fetch_graph.py, computes per-author network
metrics, and writes analysis/author_metrics.csv.

Columns:
  name, database_id, degree_weighted, degree_total,
  betweenness_weighted, betweenness_unweighted, connected_component

Run from the repo root:
  python analysis/compute_metrics.py
  python analysis/compute_metrics.py --approx 500   # faster approximate betweenness
"""

import argparse
import pickle
import time

import networkx as nx
import pandas as pd


def load_graphs():
    with open("analysis/multigraph.pkl", "rb") as f:
        MG = pickle.load(f)
    with open("analysis/graph.pkl", "rb") as f:
        G = pickle.load(f)
    return MG, G


def assign_components(G):
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    node_to_component = {}
    for idx, component in enumerate(components):
        for node in component:
            node_to_component[node] = idx
    return node_to_component


def compute_metrics(MG=None, G=None, out_path=None, approx_k=None):
    if MG is None or G is None:
        print("Loading graphs...")
        MG, G = load_graphs()
    print(f"  MultiGraph:     {MG.number_of_nodes():,} nodes, {MG.number_of_edges():,} edges")
    print(f"  Weighted Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    if out_path is None:
        out_path = "analysis/author_metrics.csv"

    print("\nComputing degree_weighted (unique coauthors)...")
    degree_weighted = dict(G.degree())

    print("Computing degree_total (all paper edges)...")
    degree_total = dict(MG.degree())

    print("Computing connected components...")
    components = assign_components(G)
    num_components = max(components.values()) + 1 if components else 0
    print(f"  {num_components:,} components")

    k_arg = {"k": approx_k} if approx_k else {}
    label = f"approximate (k={approx_k})" if approx_k else "exact"

    print(f"\nComputing betweenness_weighted ({label})...")
    t0 = time.time()
    betweenness_weighted = nx.betweenness_centrality(G, weight="distance", **k_arg)
    print(f"  Done in {time.time() - t0:.1f}s")

    print(f"Computing betweenness_unweighted ({label})...")
    t0 = time.time()
    betweenness_unweighted = nx.betweenness_centrality(G, **k_arg)
    print(f"  Done in {time.time() - t0:.1f}s")

    print("Computing clustering_unweighted...")
    clustering_unweighted = nx.clustering(G)
    print("Computing clustering_weighted...")
    clustering_weighted = nx.clustering(G, weight="weight")

    print("\nBuilding DataFrame...")
    rows = []
    for node_id, data in G.nodes(data=True):
        rows.append({
            "name": data["name"],
            "database_id": node_id,
            "degree_weighted": degree_weighted.get(node_id, 0),
            "degree_total": degree_total.get(node_id, 0),
            "betweenness_weighted": betweenness_weighted.get(node_id, 0.0),
            "betweenness_unweighted": betweenness_unweighted.get(node_id, 0.0),
            "clustering_unweighted": clustering_unweighted.get(node_id, 0.0),
            "clustering_weighted": clustering_weighted.get(node_id, 0.0),
            "connected_component": components.get(node_id, -1),
        })

    df = pd.DataFrame(rows).sort_values("betweenness_unweighted", ascending=False)
    df.to_csv(out_path, index=False)
    print(f"\nWrote {len(df):,} rows to {out_path}")
    print(f"Largest component size: {(df['connected_component'] == 0).sum():,} authors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--approx", type=int, default=None, metavar="K",
                        help="Use approximate betweenness with K sample nodes")
    args = parser.parse_args()
    compute_metrics(out_path="analysis/author_metrics.csv", approx_k=args.approx)
