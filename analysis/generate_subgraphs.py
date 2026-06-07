"""
For each of 3 conferences (ICSA, ECSA, ICSE) and years 2016-2025 (30 partitions),
fetches the coauthorship subgraph from Neo4j, saves two pickled graphs to
analysis/graphs/, and writes per-author metrics to analysis/metrics/.

Output layout:
  analysis/graphs/{conf}_{year}_multigraph.pkl
  analysis/graphs/{conf}_{year}_graph.pkl
  analysis/metrics/{conf}_{year}_author_metrics.csv

Run from repo root:
  python analysis/generate_subgraphs.py
  python analysis/generate_subgraphs.py --approx 200
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, ".")
from database_load.database_load import getSubgraph
from analysis.fetch_graph import build_graphs_from_subgraph_df, save_graphs
from analysis.compute_metrics import compute_metrics

CONFERENCES = ["icsa", "ecsa", "icse"]
YEARS = list(range(2016, 2026))
GRAPHS_DIR = "analysis/graphs"
METRICS_DIR = "analysis/metrics"


def generate_all(approx_k=None):
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)

    total = len(CONFERENCES) * len(YEARS)
    done = 0

    for conf in CONFERENCES:
        for year in YEARS:
            tag = f"{conf}_{year}"
            done += 1
            print(f"\n[{done}/{total}] {conf.upper()} {year}")

            df = getSubgraph(year=year, conf=conf)
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                print("  No data — skipping.")
                continue

            MG, G = build_graphs_from_subgraph_df(df)
            print(f"  MultiGraph: {MG.number_of_nodes():,} nodes, {MG.number_of_edges():,} edges")
            print(f"  Graph:      {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

            mg_path = os.path.join(GRAPHS_DIR, f"{tag}_multigraph.pkl")
            g_path  = os.path.join(GRAPHS_DIR, f"{tag}_graph.pkl")
            save_graphs(MG, G, mg_path, g_path)
            print(f"  Saved graphs -> {mg_path}, {g_path}")

            metrics_path = os.path.join(METRICS_DIR, f"{tag}_author_metrics.csv")
            compute_metrics(MG=MG, G=G, out_path=metrics_path, approx_k=approx_k)

    print(f"\nDone. Processed {done} partitions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--approx", type=int, default=None, metavar="K",
                        help="Use approximate betweenness with K sample nodes (faster)")
    args = parser.parse_args()
    generate_all(approx_k=args.approx)
