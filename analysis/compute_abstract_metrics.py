"""
compute_abstract_metrics.py

Computes eight abstract structural metrics for the co-authorship network.
Each task is self-contained; results are written to:

    analysis/abstract_metrics/   <- CSV tables
    analysis/plots/              <- PNG figures

Tasks
-----
  5  Power-law / scale-free degree-distribution test
  6  Small-world coefficient (exact BFS; ~90 s on the giant component)
  7  Degree assortativity  (full graph scalar + per-conference time series)
  8  Temporal role transitions across yearly conference subgraphs
  9  Community persistence (Louvain + Jaccard across consecutive years)
  10 Conference cross-pollination (fraction of ICSA/ECSA authors at ICSE)
  11 K-shell (k-core) decomposition of the full graph
  12 Author entry/exit cohort / retention-curve analysis

Run from the repo root:
    python analysis/compute_abstract_metrics.py
    python analysis/compute_abstract_metrics.py --tasks 5 7 11
"""

import argparse
import math
import os
import pickle
import time
import warnings

import matplotlib
matplotlib.use("Agg")          # non-interactive backend; avoids display dependency
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import networkx as nx
import numpy as np
import pandas as pd
import powerlaw
from networkx.algorithms.community import louvain_communities

warnings.filterwarnings("ignore", category=UserWarning)

# ─── Paths ────────────────────────────────────────────────────────────────────

METRICS_CSV    = "analysis/author_metrics.csv"
ROLES_CSV      = "analysis/author_roles.csv"
GRAPH_PKL      = "analysis/graph.pkl"
SUBGRAPH_DIR   = "analysis/graphs"
SUBMETRICS_DIR = "analysis/metrics"
OUT_DIR        = "analysis/abstract_metrics"
PLOTS_DIR      = "analysis/plots"

CONFERENCES = ["icsa", "ecsa", "icse"]
YEARS       = list(range(2016, 2026))

# Percentile thresholds — must mirror classify_roles.py
HIGH, LOW = 75, 25

CONF_COLORS = {"icsa": "steelblue", "ecsa": "coral", "icse": "mediumseagreen"}


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _mkdirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)


def _load_full_graph():
    with open(GRAPH_PKL, "rb") as fh:
        return pickle.load(fh)


def _load_sub_graph(conf, year):
    """Return the per-(conf, year) Graph pkl, or None if the file is absent."""
    path = os.path.join(SUBGRAPH_DIR, f"{conf}_{year}_graph.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return pickle.load(fh)


def _load_sub_metrics(conf, year):
    """Return the per-(conf, year) author-metrics DataFrame, or None if absent."""
    path = os.path.join(SUBMETRICS_DIR, f"{conf}_{year}_author_metrics.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def _classify_row(row, thr):
    """
    Assign a structural role to one author row given pre-computed thresholds.

    Priority order: broker > hub > embedded > peripheral > core.
    Thresholds are passed in as a dict so this function can be used with
    both global and per-snapshot threshold sets.
    """
    b_hi = row["betweenness_unweighted"] >= thr["b_hi"]
    b_lo = row["betweenness_unweighted"] <  thr["b_lo"]
    d_hi = row["degree_weighted"]        >= thr["d_hi"]
    d_lo = row["degree_weighted"]        <  thr["d_lo"]
    c_hi = row["clustering_unweighted"]  >= thr["c_hi"]
    c_lo = row["clustering_unweighted"]  <  thr["c_lo"]

    if b_hi and c_lo:  return "broker"
    if d_hi and c_lo:  return "hub"
    if c_hi and b_lo:  return "embedded"
    if d_lo:           return "peripheral"
    return "core"


def _classify_df(df):
    """
    Classify every row in a metrics DataFrame using percentile thresholds
    derived from that same DataFrame.  Roles are therefore relative to the
    given network snapshot, not the full graph — essential for fair
    longitudinal comparison across years and conferences.
    """
    thr = {
        "b_hi": df["betweenness_unweighted"].quantile(HIGH / 100),
        "b_lo": df["betweenness_unweighted"].quantile(LOW  / 100),
        "d_hi": df["degree_weighted"].quantile(HIGH / 100),
        "d_lo": df["degree_weighted"].quantile(LOW  / 100),
        "c_hi": df["clustering_unweighted"].quantile(HIGH / 100),
        "c_lo": df["clustering_unweighted"].quantile(LOW  / 100),
    }
    return df.apply(lambda row: _classify_row(row, thr), axis=1)


# ─── Task 5: Power-law / scale-free test ──────────────────────────────────────

def task5_powerlaw(G):
    """
    Test whether the degree distribution P(k) ~ k^{-alpha} follows a power law.

    Scale-free networks arise from preferential attachment (Barabasi-Albert):
    new authors disproportionately attach to already-prolific researchers,
    producing a heavy tail.  We use the `powerlaw` package (Alstott et al.,
    2014, PLOS ONE) which estimates alpha via maximum likelihood and selects
    x_min by minimising the Kolmogorov-Smirnov statistic.

    We compare the power-law fit against a log-normal alternative via a
    log-likelihood ratio test:
        R > 0  ->  power law is the better fit
        R < 0  ->  log-normal is the better fit

    Plot: Complementary CDF (CCDF) on log-log axes with fitted power-law line.
    CCDF is preferred over PDF for heavy-tailed data because it is less noisy.

    Output: analysis/plots/task5_degree_powerlaw.png
    """
    print("\n--- Task 5: Power-law test ---")
    degrees = np.array([d for _, d in G.degree() if d > 0])

    fit   = powerlaw.Fit(degrees, discrete=True)
    alpha = fit.power_law.alpha
    xmin  = fit.power_law.xmin
    ks_D  = fit.power_law.D
    R, p  = fit.distribution_compare("power_law", "lognormal")

    print(f"  alpha (exponent)   : {alpha:.4f}")
    print(f"  x_min              : {xmin}")
    print(f"  KS distance D      : {ks_D:.4f}")
    print(f"  LR vs log-normal   : R={R:.4f}, p={p:.4f}")
    print(f"  Verdict            : {'Power law preferred' if R > 0 else 'Log-normal preferred'}")

    # Empirical CCDF: P(K >= k)
    n         = len(degrees)
    unique_d  = np.sort(np.unique(degrees))
    ccdf_emp  = np.array([np.sum(degrees >= k) / n for k in unique_d])

    # Fitted power-law CCDF for k >= x_min:
    #   P(K >= k) = P(K >= x_min) * (k / x_min)^{-(alpha - 1)}
    mask    = unique_d >= xmin
    x_fit   = unique_d[mask].astype(float)
    scale   = np.sum(degrees >= xmin) / n
    y_fit   = scale * (x_fit / xmin) ** (-(alpha - 1))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(unique_d, ccdf_emp, s=8, alpha=0.6, color="steelblue",
               zorder=3, label="Empirical CCDF")
    ax.plot(x_fit, y_fit, "r--", linewidth=2,
            label=f"Power law fit (alpha={alpha:.2f}, x_min={xmin:.0f})")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Degree k  (unique co-authors)", fontsize=11)
    ax.set_ylabel("P(K >= k)", fontsize=11)
    ax.set_title("Degree Distribution CCDF (log-log)", fontsize=13)
    ax.legend(fontsize=10); ax.grid(True, which="both", alpha=0.2)

    path = os.path.join(PLOTS_DIR, "task5_degree_powerlaw.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return {"alpha": alpha, "xmin": int(xmin), "KS_D": ks_D, "LR_R": R, "LR_p": p}


# ─── Task 6: Small-world coefficient ──────────────────────────────────────────

def task6_smallworld(G):
    """
    Compute the small-world coefficient sigma on the giant connected component.

    Watts & Strogatz (1998) define a small-world network as one with:
      - clustering coefficient C much larger than C_rand (dense local groups)
      - average path length L only slightly larger than L_rand (global reachability)

    Two metrics are computed:
      sigma = (C / C_rand) / (L / L_rand)   -- sigma >> 1 => small-world
      omega = (L_rand / L) - (C / C_rand)   -- omega ~ 0  => small-world
                                                (Humphries & Gurney, 2008)

    Random-graph (Erdos-Renyi) baselines for a graph with n nodes and mean degree <k>:
      C_rand ~ <k> / n
      L_rand ~ ln(n) / ln(<k>)

    NOTE: nx.average_shortest_path_length performs exact BFS from every node.
    Runtime is approximately 90 s for the giant component (~10 k nodes).
    """
    print("\n--- Task 6: Small-world coefficient ---")
    giant_nodes = max(nx.connected_components(G), key=len)
    giant  = G.subgraph(giant_nodes).copy()
    n      = giant.number_of_nodes()
    m      = giant.number_of_edges()
    mean_k = 2 * m / n
    print(f"  Giant component: {n:,} nodes, {m:,} edges, <k>={mean_k:.3f}")

    print("  Computing average clustering coefficient...")
    C = nx.average_clustering(giant)
    print(f"  C = {C:.6f}")

    print("  Computing average shortest path length (exact BFS, ~90 s)...")
    t0 = time.time()
    L  = nx.average_shortest_path_length(giant)
    print(f"  L = {L:.4f}  ({time.time()-t0:.1f}s)")

    C_rand = mean_k / n
    L_rand = math.log(n) / math.log(mean_k)
    sigma  = (C / C_rand) / (L / L_rand)
    omega  = (L_rand / L) - (C / C_rand)

    print(f"\n  Random (ER) baseline:  C_rand={C_rand:.6f},  L_rand={L_rand:.4f}")
    print(f"  sigma = {sigma:.4f}   (>> 1 => small-world)")
    print(f"  omega = {omega:.4f}   (~  0 => small-world)")
    print(f"  Verdict: {'Small-world' if sigma > 1 else 'Not small-world'}")

    return {"n": n, "m": m, "mean_k": mean_k,
            "C": C, "L": L, "C_rand": C_rand, "L_rand": L_rand,
            "sigma": sigma, "omega": omega}


# ─── Task 7: Degree assortativity ─────────────────────────────────────────────

def task7_assortativity(G):
    """
    Measure degree assortativity r (Newman, 2002) for the full graph and track
    it over time for each conference using the 29 subgraph pkl files.

    r in [-1, 1]:
      r > 0  (assortative)   -- hubs cluster together; "rich-club" behaviour
      r < 0  (disassortative)-- hubs connect to low-degree periphery
      r ~ 0                  -- no degree-degree correlation

    In co-authorship networks, mild positive assortativity is common because
    prolific researchers tend to lead large collaborative groups.  A negative r
    would indicate brokers actively recruit peripheral authors.

    Additional analysis:
    Assortativity is computed for all 29 (conf, year) subgraphs and plotted
    as a time series, enabling detection of structural shifts over time.

    Outputs:
      analysis/abstract_metrics/task7_assortativity_by_year.csv
      analysis/plots/task7_assortativity_trends.png
    """
    print("\n--- Task 7: Degree assortativity ---")
    r_global = nx.degree_assortativity_coefficient(G)
    print(f"  Full-graph r = {r_global:.4f}")

    records = []
    for conf in CONFERENCES:
        for year in YEARS:
            Gs = _load_sub_graph(conf, year)
            if Gs is None or Gs.number_of_edges() == 0:
                continue
            r = nx.degree_assortativity_coefficient(Gs)
            records.append({"conference": conf, "year": year, "assortativity": r})

    df = pd.DataFrame(records)

    # Per-conference summary
    for conf in CONFERENCES:
        sub = df[df["conference"] == conf]["assortativity"]
        print(f"  {conf.upper()}: mean r={sub.mean():.4f}, range [{sub.min():.4f}, {sub.max():.4f}]")

    csv_path = os.path.join(OUT_DIR, "task7_assortativity_by_year.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    fig, ax = plt.subplots(figsize=(10, 5))
    for conf in CONFERENCES:
        sub = df[df["conference"] == conf].sort_values("year")
        ax.plot(sub["year"], sub["assortativity"], marker="o",
                color=CONF_COLORS[conf], linewidth=2, label=conf.upper())
    ax.axhline(r_global, color="gray", linestyle="--", alpha=0.7,
               label=f"Full graph (r={r_global:.3f})")
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Degree Assortativity (r)", fontsize=11)
    ax.set_title("Degree Assortativity by Conference and Year", fontsize=13)
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    ax.set_xticks(YEARS); ax.set_xticklabels(YEARS, rotation=45)

    path = os.path.join(PLOTS_DIR, "task7_assortativity_trends.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return r_global, df


# ─── Task 8: Temporal role transitions ────────────────────────────────────────

def task8_role_transitions():
    """
    For each (conference, year) snapshot, classify every author into a
    structural role using per-snapshot percentile thresholds (not global ones),
    so the classification is meaningful relative to that year's network.

    Roles: broker, hub, embedded, peripheral, core  (same logic as classify_roles.py)

    For each author appearing in two consecutive years at the same conference,
    record the role transition: role_t -> role_{t+1}.  Skipped years are not
    counted as transitions (the author must appear in BOTH year t and year t+1).

    Primary output (per-author per-year):
      analysis/abstract_metrics/task8_author_roles_by_year.csv

    Additional analysis (since primary output is a large per-row table):
      1. Transition probability matrix (5x5):
           task8_transition_matrix.csv
           task8_transition_heatmap.png
      2. Role proportion over time per conference:
           task8_role_proportions.png
    """
    print("\n--- Task 8: Temporal role transitions ---")
    ROLES = ["broker", "hub", "embedded", "peripheral", "core"]

    # Step 1: classify roles for every (conf, year) snapshot
    rows = []
    for conf in CONFERENCES:
        for year in YEARS:
            df = _load_sub_metrics(conf, year)
            if df is None or df.empty:
                continue
            df = df.copy()
            df["role"] = _classify_df(df)
            for _, r in df[["name", "role"]].iterrows():
                rows.append({"name": r["name"], "conference": conf,
                             "year": year, "role": r["role"]})

    role_df = pd.DataFrame(rows)
    csv_path = os.path.join(OUT_DIR, "task8_author_roles_by_year.csv")
    role_df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}  ({len(role_df):,} rows)")

    # Step 2: count consecutive-year role transitions per author-conference
    # Only pairs (t, t+1) where the author appears in BOTH years are counted.
    trans_counts = pd.DataFrame(0, index=ROLES, columns=ROLES, dtype=int)

    for (name, conf), grp in role_df.sort_values("year").groupby(["name", "conference"]):
        role_map = dict(zip(grp["year"], grp["role"]))
        for year in sorted(role_map):
            if year + 1 in role_map:
                src, dst = role_map[year], role_map[year + 1]
                if src in ROLES and dst in ROLES:
                    trans_counts.loc[src, dst] += 1

    # Normalise rows to get per-role transition probabilities
    row_sums  = trans_counts.sum(axis=1).replace(0, np.nan)
    trans_prob = trans_counts.div(row_sums, axis=0).fillna(0)

    matrix_path = os.path.join(OUT_DIR, "task8_transition_matrix.csv")
    trans_prob.to_csv(matrix_path)
    print(f"  Saved: {matrix_path}")
    total_trans = int(trans_counts.values.sum())
    print(f"  Total transitions counted: {total_trans:,}")

    # Diagonal (stability) rates
    for role in ROLES:
        p_stable = trans_prob.loc[role, role] if role in trans_prob.index else 0
        print(f"    P(stay {role:10s}) = {p_stable:.3f}")

    # Heatmap of transition probabilities
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(trans_prob.values, cmap="Blues", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Transition probability")
    ax.set_xticks(range(len(ROLES))); ax.set_xticklabels(ROLES, rotation=45, ha="right")
    ax.set_yticks(range(len(ROLES))); ax.set_yticklabels(ROLES)
    ax.set_xlabel("Role at year t+1"); ax.set_ylabel("Role at year t")
    ax.set_title("Role Transition Probabilities (consecutive years)", fontsize=13)
    for i in range(len(ROLES)):
        for j in range(len(ROLES)):
            val = trans_prob.values[i, j]
            if val > 0.01:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=8, color="white" if val > 0.55 else "black")
    path = os.path.join(PLOTS_DIR, "task8_transition_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # Role proportion over time — one sub-plot per conference
    role_colors = {"broker": "tomato", "hub": "orange", "embedded": "gold",
                   "peripheral": "lightblue", "core": "steelblue"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, conf in zip(axes, CONFERENCES):
        sub = role_df[role_df["conference"] == conf]
        pivot = (sub.groupby(["year", "role"]).size()
                    .unstack(fill_value=0))
        pivot = pivot.div(pivot.sum(axis=1), axis=0)   # normalise to proportions
        for role in ROLES:
            if role in pivot.columns:
                ax.plot(pivot.index, pivot[role], marker="o", linewidth=1.5,
                        label=role, color=role_colors[role])
        ax.set_title(conf.upper()); ax.set_xlabel("Year")
        ax.set_xticks(YEARS); ax.set_xticklabels(YEARS, rotation=45)
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("Proportion of authors")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", fontsize=9, title="Role",
               bbox_to_anchor=(1.02, 1))
    fig.suptitle("Role Composition per Conference over Time", fontsize=13)
    path = os.path.join(PLOTS_DIR, "task8_role_proportions.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return role_df, trans_prob


# ─── Task 9: Community persistence ────────────────────────────────────────────

def task9_community_persistence():
    """
    Measure how stable research communities are across consecutive years.

    Method:
      1. Detect communities in year t using Louvain (seed=42 for reproducibility).
      2. Detect communities in year t+1 using the same method.
      3. For each community C_i in year t, find the best-match community D_j
         in year t+1 by maximising Jaccard(C_i, D_j) = |C_i & D_j| / |C_i | D_j|.
      4. Average the best-match Jaccard scores across all communities in year t.
         This "mean persistence score" lies in [0, 1]:
           near 1  -> communities are nearly identical year-over-year
           near 0  -> complete community reorganisation

    Nodes are matched by author name across years (same key used in subgraph CSVs).

    Output: analysis/plots/task9_community_persistence.png
    """
    print("\n--- Task 9: Community persistence ---")

    def best_match_jaccard(comm, comms_next):
        """Best Jaccard similarity of comm against any community in comms_next."""
        if not comm:
            return 0.0
        best = 0.0
        for other in comms_next:
            inter = len(comm & other)
            if inter:
                best = max(best, inter / len(comm | other))
        return best

    records = []
    for conf in CONFERENCES:
        for i, year in enumerate(YEARS[:-1]):
            next_year = YEARS[i + 1]
            G1 = _load_sub_graph(conf, year)
            G2 = _load_sub_graph(conf, next_year)
            if G1 is None or G2 is None:
                continue

            comms1 = [set(c) for c in louvain_communities(G1, seed=42, weight="weight")]
            comms2 = [set(c) for c in louvain_communities(G2, seed=42, weight="weight")]

            scores  = [best_match_jaccard(c, comms2) for c in comms1]
            mean_j  = float(np.mean(scores))
            records.append({
                "conference": conf, "year_start": year,
                "mean_jaccard": mean_j, "n_communities": len(comms1),
            })
            print(f"  {conf.upper()} {year}->{next_year}: "
                  f"mean_jaccard={mean_j:.4f}  ({len(comms1)} communities)")

    df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(10, 5))
    for conf in CONFERENCES:
        sub = df[df["conference"] == conf].sort_values("year_start")
        # plot at midpoint between year_start and year_start+1
        ax.plot(sub["year_start"] + 0.5, sub["mean_jaccard"], marker="o",
                color=CONF_COLORS[conf], linewidth=2, label=conf.upper())
    ax.set_xlabel("Year transition", fontsize=11)
    ax.set_ylabel("Mean best-match Jaccard", fontsize=11)
    ax.set_title("Community Persistence Across Consecutive Years", fontsize=13)
    ax.set_ylim(0, None); ax.legend(); ax.grid(axis="y", alpha=0.3)
    tick_positions = [y + 0.5 for y in YEARS[:-1]]
    tick_labels    = [f"{y}->{y+1}" for y in YEARS[:-1]]
    ax.set_xticks(tick_positions); ax.set_xticklabels(tick_labels, rotation=45)

    path = os.path.join(PLOTS_DIR, "task9_community_persistence.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return df


# ─── Task 10: Conference cross-pollination ─────────────────────────────────────

def task10_cross_pollination():
    """
    For each year, measure the fraction of ICSA and ECSA authors who also
    published at ICSE in the same year.

    Cross-pollination captures the degree to which the software-architecture
    community (ICSA, ECSA) overlaps with the broader SE community (ICSE).
    An increasing trend suggests convergence; a decrease indicates specialisation.

    Author identity is matched by name string — the same approach used throughout
    the pipeline (author names are unique keys in the Neo4j graph).

    Output: analysis/plots/task10_cross_pollination.png
    """
    print("\n--- Task 10: Conference cross-pollination ---")
    records = []

    for year in YEARS:
        icse_df = _load_sub_metrics("icse", year)
        if icse_df is None:
            continue
        icse_names = set(icse_df["name"].dropna())

        for conf in ["icsa", "ecsa"]:
            sub = _load_sub_metrics(conf, year)
            if sub is None:
                continue
            conf_names = set(sub["name"].dropna())
            n_overlap  = len(conf_names & icse_names)
            frac       = n_overlap / len(conf_names) if conf_names else 0.0
            records.append({
                "conference": conf, "year": year,
                "n_conf_authors": len(conf_names),
                "n_also_at_icse": n_overlap,
                "fraction_at_icse": frac,
            })
            print(f"  {conf.upper()} {year}: {n_overlap}/{len(conf_names)} "
                  f"also at ICSE ({frac:.1%})")

    df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(10, 5))
    for conf in ["icsa", "ecsa"]:
        sub = df[df["conference"] == conf].sort_values("year")
        ax.plot(sub["year"], sub["fraction_at_icse"] * 100,
                marker="o", color=CONF_COLORS[conf], linewidth=2,
                label=conf.upper())
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("% of authors also publishing at ICSE", fontsize=11)
    ax.set_title("Cross-pollination: ICSA / ECSA Authors Also at ICSE", fontsize=13)
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    ax.set_xticks(YEARS); ax.set_xticklabels(YEARS, rotation=45)

    path = os.path.join(PLOTS_DIR, "task10_cross_pollination.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return df


# ─── Task 11: K-shell decomposition ───────────────────────────────────────────

def task11_kshell(G):
    """
    Assign every author to their k-core number (k-shell index).

    The k-core of a graph is the maximal subgraph in which every node has
    at least k neighbours.  A node's k-shell index is the highest k for which
    it is still included.  Unlike the role taxonomy (which uses percentile
    thresholds), k-shell is a parameter-free topological measure:
      low k-shell  -> structurally peripheral (weakly embedded)
      high k-shell -> belongs to the dense "nucleus" of the network

    Primary output (per-author):
      analysis/abstract_metrics/task11_author_kshell.csv

    Additional analysis:
      - Histogram of k-shell distribution
      - Boxplot of k-shell grouped by structural role (from author_roles.csv)
    """
    print("\n--- Task 11: K-shell decomposition ---")
    core_numbers = nx.core_number(G)
    max_k = max(core_numbers.values())
    print(f"  Max k-shell: {max_k}")

    from collections import Counter
    dist = Counter(core_numbers.values())
    print("  Top-5 k-shell levels by author count:")
    for k, cnt in sorted(dist.items(), reverse=True)[:5]:
        print(f"    k={k:3d}  {cnt:,} authors")

    # Merge k-shell into the full author metrics + roles table
    metrics = pd.read_csv(METRICS_CSV)
    roles   = pd.read_csv(ROLES_CSV)[["name", "role"]]

    # In the full graph, node keys are Neo4j element IDs stored in 'database_id'
    metrics["k_shell"] = metrics["database_id"].map(core_numbers)
    df = metrics.merge(roles, on="name", how="left")

    csv_path = os.path.join(OUT_DIR, "task11_author_kshell.csv")
    df[["name", "database_id", "degree_weighted", "betweenness_unweighted",
        "clustering_unweighted", "k_shell", "role"]].to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    # Print authors in the highest k-shell, ranked by betweenness
    top_k = df[df["k_shell"] == max_k].sort_values("betweenness_unweighted", ascending=False)
    print(f"\n  Authors in the highest k-shell (k={max_k}), ranked by betweenness:")
    print(top_k[["name", "degree_weighted", "betweenness_unweighted", "role"]]
              .head(10).to_string(index=False))

    # K-shell histogram
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(list(core_numbers.values()),
            bins=range(0, max_k + 2), color="steelblue",
            edgecolor="white", alpha=0.85)
    ax.set_xlabel("K-shell index", fontsize=11)
    ax.set_ylabel("Number of authors", fontsize=11)
    ax.set_title("K-shell Distribution (full co-authorship graph)", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    path = os.path.join(PLOTS_DIR, "task11_kshell_histogram.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # K-shell by role — boxplot
    # Order roles from least to most structurally embedded
    role_order  = ["peripheral", "embedded", "core", "hub", "broker"]
    role_palette = {"peripheral": "lightblue", "embedded": "gold",
                    "core": "steelblue", "hub": "orange", "broker": "tomato"}
    data_by_role = [df[df["role"] == r]["k_shell"].dropna().values for r in role_order]
    present      = [(r, d) for r, d in zip(role_order, data_by_role) if len(d) > 0]

    fig, ax = plt.subplots(figsize=(8, 5))
    bp = ax.boxplot([d for _, d in present],
                    labels=[r for r, _ in present],
                    patch_artist=True,
                    medianprops={"color": "black", "linewidth": 2})
    for patch, (role, _) in zip(bp["boxes"], present):
        patch.set_facecolor(role_palette.get(role, "lightgray"))
    ax.set_xlabel("Structural role", fontsize=11)
    ax.set_ylabel("K-shell index", fontsize=11)
    ax.set_title("K-shell Index by Structural Role", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    path = os.path.join(PLOTS_DIR, "task11_kshell_by_role.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return df


# ─── Task 12: Entry/exit cohort / retention analysis ──────────────────────────

def task12_retention():
    """
    Track when each author first and last appears at each conference and compute
    mean retention (survival) curves per conference.

    Definitions:
      debut_year   = first year the author appears in the conference subgraph
      exit_year    = last observed year
      years_active = number of distinct years with at least one publication

    Retention curve construction:
      For each debut cohort Y, the retention at lag t is:
        R(Y, t) = |{a in cohort_Y : a appears in year Y+t}| / |cohort_Y|

      The mean retention curve averages R(Y, t) across all cohorts, weighted
      by cohort size.  Only lags for which we have actual follow-up data
      (i.e., the subgraph CSV for year Y+t exists) are counted.

    Primary output (per-author summary):
      analysis/abstract_metrics/task12_author_cohorts.csv
    Plot:
      analysis/plots/task12_retention_curves.png
    """
    print("\n--- Task 12: Entry/exit cohort analysis ---")

    # Build {(author_name, conf): sorted list of years present}
    presence: dict = {}
    for conf in CONFERENCES:
        for year in YEARS:
            df = _load_sub_metrics(conf, year)
            if df is None or df.empty:
                continue
            for name in df["name"].dropna():
                presence.setdefault((name, conf), []).append(year)

    # Summarise into one row per (author, conference)
    cohort_rows = []
    for (name, conf), yrs in presence.items():
        yrs = sorted(set(yrs))
        cohort_rows.append({
            "name": name, "conference": conf,
            "debut_year":    yrs[0],
            "exit_year":     yrs[-1],
            "years_active":  len(yrs),
            "career_span":   yrs[-1] - yrs[0] + 1,
        })
    cohort_df = pd.DataFrame(cohort_rows)

    csv_path = os.path.join(OUT_DIR, "task12_author_cohorts.csv")
    cohort_df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}  ({len(cohort_df):,} author-conference pairs)")

    # Convert to set lookup for fast membership testing
    presence_set = {k: set(v) for k, v in presence.items()}

    max_lag = 9   # 2016 debut -> 2025 is 9 years of follow-up

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, conf in zip(axes, CONFERENCES):
        conf_df      = cohort_df[cohort_df["conference"] == conf]
        debut_years  = sorted(conf_df["debut_year"].unique())

        lag_num = {}   # lag -> total authors still present (numerator)
        lag_den = {}   # lag -> total authors who could have been seen (denominator)

        for debut in debut_years:
            cohort_names = conf_df[conf_df["debut_year"] == debut]["name"].tolist()
            n = len(cohort_names)
            for lag in range(1, max_lag + 1):
                follow_year = debut + lag
                if follow_year > YEARS[-1]:
                    break
                # Only count this cohort/lag if we actually have data for follow_year
                if _load_sub_metrics(conf, follow_year) is None:
                    continue
                still = sum(
                    1 for name in cohort_names
                    if follow_year in presence_set.get((name, conf), set())
                )
                lag_num[lag] = lag_num.get(lag, 0) + still
                lag_den[lag] = lag_den.get(lag, 0) + n

        lags  = sorted(lag_num.keys())
        rates = [lag_num[l] / lag_den[l] for l in lags]

        if rates:
            print(f"  {conf.upper()} -- 1-yr retention: {rates[0]:.1%}"
                  + (f",  3-yr: {rates[2]:.1%}" if len(rates) > 2 else "")
                  + (f",  5-yr: {rates[4]:.1%}" if len(rates) > 4 else ""))

        ax.plot(lags, rates, marker="o", color=CONF_COLORS[conf], linewidth=2)
        ax.fill_between(lags, 0, rates, alpha=0.12, color=CONF_COLORS[conf])
        ax.set_title(conf.upper(), fontsize=12)
        ax.set_xlabel("Years since debut", fontsize=10)
        ax.set_ylim(0, 0.6); ax.set_xticks(range(1, max_lag + 1))
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Retention rate", fontsize=11)
    fig.suptitle(
        "Author Retention by Conference (mean across all debut cohorts, 2016-2025)",
        fontsize=13)
    path = os.path.join(PLOTS_DIR, "task12_retention_curves.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    return cohort_df


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(tasks=None):
    _mkdirs()

    ALL = {5, 6, 7, 8, 9, 10, 11, 12}
    run = ALL if tasks is None else set(tasks)

    print("Loading full co-authorship graph...")
    G = _load_full_graph()
    print(f"  {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    results = {}

    if  5 in run: results[5]  = task5_powerlaw(G)
    if  6 in run: results[6]  = task6_smallworld(G)
    if  7 in run: results[7]  = task7_assortativity(G)
    if  8 in run: results[8]  = task8_role_transitions()
    if  9 in run: results[9]  = task9_community_persistence()
    if 10 in run: results[10] = task10_cross_pollination()
    if 11 in run: results[11] = task11_kshell(G)
    if 12 in run: results[12] = task12_retention()

    print("\n=== All tasks complete ===")
    print(f"  Plots  -> {PLOTS_DIR}/")
    print(f"  Tables -> {OUT_DIR}/")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute abstract network metrics")
    parser.add_argument("--tasks", nargs="+", type=int, default=None, metavar="N",
                        help="Subset of task numbers to run (default: all 5-12)")
    args = parser.parse_args()
    main(tasks=args.tasks)
