"""
compute_trivial_metrics.py

Computes four descriptive / summary metrics directly from the pre-built CSV files
produced by the pipeline.  No graph loading or heavy computation is required —
every task reads one CSV, aggregates, and either prints scalars or saves a plot.

Tasks
-----
  1  Author centrality summary  (author_metrics.csv)
  2  Structural role distribution  (author_roles.csv)
  3  Community size distribution  (author_communities.csv)
  4  Cross-conference bridge authors  (bridge_authors.csv)

Run from the repo root:
    python analysis/compute_trivial_metrics.py
    python analysis/compute_trivial_metrics.py --tasks 1 3
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────

METRICS_CSV    = "analysis/author_metrics.csv"
ROLES_CSV      = "analysis/author_roles.csv"
COMMUNITIES_CSV = "analysis/author_communities.csv"
BRIDGE_CSV     = "analysis/bridge_authors.csv"
PLOTS_DIR      = "analysis/plots"

ROLE_ORDER  = ["peripheral", "core", "broker"]
ROLE_COLORS = {"peripheral": "lightblue", "core": "steelblue", "broker": "tomato"}

CONF_COLORS = {"icsa": "steelblue", "ecsa": "coral", "icse": "mediumseagreen"}


def _mkdirs():
    os.makedirs(PLOTS_DIR, exist_ok=True)


# ─── Task 1: Author centrality summary ────────────────────────────────────────

def task1_centrality_summary():
    """
    Summarise the three primary centrality measures across all 13,903 authors:
      - degree_weighted    : total co-authorship weight (sum of shared-paper counts)
      - betweenness_unweighted : fraction of shortest paths passing through the node
      - clustering_unweighted  : proportion of a node's neighbours that are mutual neighbours

    Printed outputs:
      - Mean / median / max for each metric
      - Top-10 authors by weighted degree (most prolific collaborators)
      - Top-10 authors by unweighted betweenness (strongest structural bridges)
      - Connected-components breakdown: how many components, size of the giant

    Plot: weighted-degree histogram (log-y scale) to show the heavy tail.

    Output: analysis/plots/task1_degree_histogram.png
    """
    print("\n--- Task 1: Author centrality summary ---")
    df = pd.read_csv(METRICS_CSV)
    n  = len(df)

    for col, label in [
        ("degree_weighted",       "Weighted degree"),
        ("betweenness_unweighted","Betweenness (unweighted)"),
        ("clustering_unweighted", "Clustering (unweighted)"),
    ]:
        s = df[col]
        print(f"\n  {label}:")
        print(f"    mean   = {s.mean():.4f}")
        print(f"    median = {s.median():.4f}")
        print(f"    max    = {s.max():.4f}  ({df.loc[s.idxmax(), 'name']})")

    print(f"\n  Top-10 authors by weighted degree:")
    top_deg = df.nlargest(10, "degree_weighted")[["name", "degree_weighted",
                                                   "betweenness_unweighted",
                                                   "clustering_unweighted"]]
    print(top_deg.to_string(index=False))

    print(f"\n  Top-10 authors by betweenness (unweighted):")
    top_bet = df.nlargest(10, "betweenness_unweighted")[["name", "betweenness_unweighted",
                                                          "degree_weighted"]]
    print(top_bet.to_string(index=False))

    # Connected components: report how many components and the giant's size.
    # connected_component column stores the component index (0 = giant in most pipelines).
    comp_sizes = df["connected_component"].value_counts().sort_values(ascending=False)
    n_comps    = len(comp_sizes)
    giant_size = comp_sizes.iloc[0]
    print(f"\n  Connected components: {n_comps:,}")
    print(f"  Giant component size: {giant_size:,} authors ({giant_size/n*100:.1f}%)")
    print(f"  Isolated / tiny components: {n_comps - 1:,}")

    # Degree histogram (log-y) to expose the heavy tail
    degrees = df["degree_weighted"].values
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(degrees, bins=50, color="steelblue", edgecolor="white", alpha=0.85)
    ax.set_yscale("log")
    ax.set_xlabel("Weighted degree  (total co-authorship weight)", fontsize=11)
    ax.set_ylabel("Number of authors  (log scale)", fontsize=11)
    ax.set_title("Weighted Degree Distribution — All Authors", fontsize=13)
    ax.grid(axis="y", alpha=0.3, which="both")

    # Annotate the top author
    top_name = df.loc[df["degree_weighted"].idxmax(), "name"]
    top_val  = df["degree_weighted"].max()
    ax.annotate(
        top_name, xy=(top_val, 1), xytext=(top_val * 0.6, 5),
        arrowprops=dict(arrowstyle="->", color="gray"),
        fontsize=8, color="gray",
    )

    path = os.path.join(PLOTS_DIR, "task1_degree_histogram.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {path}")


# ─── Task 2: Structural role distribution ─────────────────────────────────────

def task2_role_distribution():
    """
    Summarise how authors are distributed across the three structural roles
    identified by the pipeline's percentile classifier:

      peripheral  -- low degree, low betweenness, low clustering
      core        -- mid-range across all three metrics
      broker      -- high betweenness, low clustering (structural bridges)

    Note: the pipeline's classify_roles.py yields only three roles for this
    dataset (hub and embedded do not meet their threshold conditions given the
    degree / clustering distribution of this particular network).

    Printed outputs:
      - Count and percentage per role
      - Median degree, betweenness, and clustering per role

    Plots:
      analysis/plots/task2_role_counts.png      — bar chart of author counts
      analysis/plots/task2_role_metrics.png     — boxplots of key metrics per role
    """
    print("\n--- Task 2: Structural role distribution ---")
    df = pd.read_csv(ROLES_CSV)
    n  = len(df)

    counts = df["role"].value_counts()
    print("\n  Role counts and percentages:")
    for role in ROLE_ORDER:
        if role in counts.index:
            c = counts[role]
            print(f"    {role:12s}  {c:5,}  ({c/n*100:.1f}%)")

    print("\n  Median metrics per role:")
    medians = df.groupby("role")[["degree_weighted",
                                   "betweenness_unweighted",
                                   "clustering_unweighted"]].median()
    print(medians.to_string())

    # Bar chart of role counts
    fig, ax = plt.subplots(figsize=(6, 4))
    roles_present = [r for r in ROLE_ORDER if r in counts.index]
    vals  = [counts[r] for r in roles_present]
    colors = [ROLE_COLORS[r] for r in roles_present]
    bars = ax.bar(roles_present, vals, color=colors, edgecolor="white", width=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 60,
                f"{val:,}", ha="center", va="bottom", fontsize=10)
    ax.set_xlabel("Structural role", fontsize=11)
    ax.set_ylabel("Number of authors", fontsize=11)
    ax.set_title("Author Distribution by Structural Role", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(vals) * 1.12)

    path = os.path.join(PLOTS_DIR, "task2_role_counts.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {path}")

    # Boxplots of degree and betweenness per role (side-by-side subplots)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, (col, label) in zip(axes, [
        ("degree_weighted",       "Weighted degree"),
        ("betweenness_unweighted","Betweenness (unweighted)"),
    ]):
        data   = [df[df["role"] == r][col].dropna().values for r in roles_present]
        bp = ax.boxplot(data, tick_labels=roles_present, patch_artist=True,
                        medianprops={"color": "black", "linewidth": 2},
                        showfliers=False)   # omit outliers to keep scale readable
        for patch, role in zip(bp["boxes"], roles_present):
            patch.set_facecolor(ROLE_COLORS[role])
        ax.set_xlabel("Structural role", fontsize=11)
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f"{label} by Role", fontsize=12)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Centrality Metrics by Structural Role (outliers hidden)", fontsize=13)
    path = os.path.join(PLOTS_DIR, "task2_role_metrics.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── Task 3: Community size distribution ──────────────────────────────────────

def task3_community_sizes():
    """
    Analyse the Louvain community structure of the full co-authorship graph.

    author_communities.csv stores one row per author with:
      community_id   -- integer label assigned by Louvain
      community_size -- number of authors in that community (stored redundantly
                        for convenience; derived from the community_id groupby)

    Key questions:
      1. How many communities are there?
      2. What does the size distribution look like — are most communities tiny,
         or do a few large "mega-communities" dominate?
      3. How much of the network is covered by the top-K communities?

    Printed outputs:
      - Total community count
      - Scalar size statistics (min, median, mean, max)
      - Fraction of authors in the top-5 communities

    Plot: community size histogram (log–log axes) to capture the wide range from
    singletons to 632-member communities.

    Output: analysis/plots/task3_community_sizes.png
    """
    print("\n--- Task 3: Community size distribution ---")
    df = pd.read_csv(COMMUNITIES_CSV)
    n  = len(df)

    # One size value per community (not per author)
    sizes = df.groupby("community_id").size().sort_values(ascending=False)
    n_comms = len(sizes)

    print(f"\n  Total communities: {n_comms:,}")
    print(f"  Size statistics:")
    print(f"    min    = {sizes.min()}")
    print(f"    median = {sizes.median():.0f}")
    print(f"    mean   = {sizes.mean():.1f}")
    print(f"    max    = {sizes.max()}  (community {sizes.idxmax()})")

    top5_total = sizes.head(5).sum()
    print(f"\n  Top-5 communities contain {top5_total:,} authors "
          f"({top5_total/n*100:.1f}% of all authors)")
    print(f"  Communities of size 1 (singletons): "
          f"{(sizes == 1).sum():,}  ({(sizes == 1).sum()/n_comms*100:.1f}% of communities)")

    print("\n  Top-10 largest communities:")
    top10 = sizes.head(10).reset_index()
    top10.columns = ["community_id", "size"]
    top10["% of network"] = (top10["size"] / n * 100).map("{:.1f}%".format)
    print(top10.to_string(index=False))

    # Histogram on log–log axes (per-community sizes, not per-author)
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.logspace(0, np.log10(sizes.max() + 1), 40)
    ax.hist(sizes.values, bins=bins, color="mediumseagreen", edgecolor="white", alpha=0.85)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Community size (number of authors)", fontsize=11)
    ax.set_ylabel("Number of communities  (log scale)", fontsize=11)
    ax.set_title("Community Size Distribution (log–log)", fontsize=13)
    ax.grid(True, which="both", alpha=0.2)

    path = os.path.join(PLOTS_DIR, "task3_community_sizes.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {path}")


# ─── Task 4: Cross-conference bridge authors ──────────────────────────────────

def task4_bridge_authors():
    """
    Analyse the 844 "bridge" authors who published at more than one conference
    (ICSA, ECSA, ICSE) across the 2016–2025 study window.

    Bridge authors are the inter-community connectors whose cross-venue activity
    links the software-architecture and general-SE research ecosystems.

    bridge_authors.csv columns:
      n_conferences          -- 2 or 3 (how many distinct venues this author appeared at)
      ICSA / ICSE / ECSA     -- publication count at each venue
      total_pubs             -- sum across venues
      degree_weighted        -- co-authorship weight in the full graph
      betweenness_unweighted -- full-graph betweenness

    Printed outputs:
      - Count of 2- vs 3-conference bridges
      - Conference-pair breakdown for 2-conference bridges (ICSA+ICSE, ICSA+ECSA, ICSE+ECSA)
      - Top-10 bridges by total publications
      - Top-10 bridges by betweenness

    Plots:
      analysis/plots/task4_bridge_conferences.png  — grouped bar of bridge counts
      analysis/plots/task4_bridge_scatter.png      — total_pubs vs betweenness scatter
    """
    print("\n--- Task 4: Cross-conference bridge authors ---")
    df = pd.read_csv(BRIDGE_CSV)
    n  = len(df)

    two_conf   = df[df["n_conferences"] == 2]
    three_conf = df[df["n_conferences"] == 3]
    print(f"\n  Total bridge authors: {n}")
    print(f"    2-conference bridges : {len(two_conf):,} ({len(two_conf)/n*100:.1f}%)")
    print(f"    3-conference bridges : {len(three_conf):,} ({len(three_conf)/n*100:.1f}%)")

    # For 2-conference bridges, determine which pair they belong to.
    # An author appears at a conference if their count for that conf > 0.
    def conf_pair(row):
        at = [c for c in ["ICSA", "ICSE", "ECSA"] if row[c] > 0]
        return "+".join(sorted(at))

    two_conf = two_conf.copy()
    two_conf["pair"] = two_conf.apply(conf_pair, axis=1)
    pair_counts = two_conf["pair"].value_counts()
    print("\n  2-conference bridge breakdown by pair:")
    for pair, cnt in pair_counts.items():
        print(f"    {pair:15s}  {cnt:,}")

    print("\n  Top-10 bridge authors by total publications:")
    top_pubs = df.nlargest(10, "total_pubs")[["name", "n_conferences",
                                               "ICSA", "ICSE", "ECSA", "total_pubs"]]
    print(top_pubs.to_string(index=False))

    print("\n  Top-10 bridge authors by betweenness:")
    top_bet = df.nlargest(10, "betweenness_unweighted")[["name", "n_conferences",
                                                          "total_pubs",
                                                          "betweenness_unweighted"]]
    print(top_bet.to_string(index=False))

    # Grouped bar: 2- vs 3-conference bridges, split by conference presence
    pair_labels  = ["ICSA+ICSE", "ECSA+ICSE", "ICSA+ECSA", "ICSA+ECSA+ICSE"]
    pair_vals    = [
        pair_counts.get("ICSA+ICSE", 0),
        pair_counts.get("ECSA+ICSE", 0),
        pair_counts.get("ECSA+ICSA", 0),  # sorted pair key
        len(three_conf),
    ]
    bar_colors   = ["steelblue", "mediumseagreen", "coral", "mediumpurple"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(pair_labels, pair_vals, color=bar_colors, edgecolor="white", width=0.55)
    for bar, val in zip(bars, pair_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 4,
                str(val), ha="center", va="bottom", fontsize=10)
    ax.set_xlabel("Conference span", fontsize=11)
    ax.set_ylabel("Number of bridge authors", fontsize=11)
    ax.set_title("Bridge Authors by Conference Span", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(pair_vals) * 1.15)

    path = os.path.join(PLOTS_DIR, "task4_bridge_conferences.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {path}")

    # Scatter: total_pubs vs betweenness, coloured by n_conferences
    fig, ax = plt.subplots(figsize=(8, 6))
    for n_conf, color, label in [(2, "steelblue", "2-conference"), (3, "tomato", "3-conference")]:
        sub = df[df["n_conferences"] == n_conf]
        ax.scatter(sub["total_pubs"], sub["betweenness_unweighted"],
                   s=20, alpha=0.5, color=color, label=label, zorder=3)

    # Label the top-5 highest-betweenness authors
    for _, row in df.nlargest(5, "betweenness_unweighted").iterrows():
        ax.annotate(row["name"], xy=(row["total_pubs"], row["betweenness_unweighted"]),
                    xytext=(4, 2), textcoords="offset points", fontsize=7, color="gray")

    ax.set_xlabel("Total publications across venues", fontsize=11)
    ax.set_ylabel("Betweenness centrality (unweighted)", fontsize=11)
    ax.set_title("Bridge Authors: Publication Volume vs. Structural Centrality", fontsize=12)
    ax.legend(fontsize=10); ax.grid(alpha=0.2)

    path = os.path.join(PLOTS_DIR, "task4_bridge_scatter.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(tasks=None):
    _mkdirs()

    ALL = {1, 2, 3, 4}
    run = ALL if tasks is None else set(tasks)

    if 1 in run: task1_centrality_summary()
    if 2 in run: task2_role_distribution()
    if 3 in run: task3_community_sizes()
    if 4 in run: task4_bridge_authors()

    print("\n=== All tasks complete ===")
    print(f"  Plots -> {PLOTS_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute trivial/descriptive network metrics")
    parser.add_argument("--tasks", nargs="+", type=int, default=None, metavar="N",
                        help="Subset of task numbers to run (default: all 1-4)")
    args = parser.parse_args()
    main(tasks=args.tasks)
