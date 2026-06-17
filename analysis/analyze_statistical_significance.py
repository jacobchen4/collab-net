"""
Statistical comparison of author collaboration-network metrics across the
ICSE, ICSA and ECSA conferences over 2015-2025.

Scope: the three *weighted* per-author metrics
    - degree_weighted        (raw count of unique coauthors; scales with network size)
    - betweenness_weighted   (networkx-normalized to [0, 1])
    - clustering_weighted    (inherently in [0, 1])

Unit of analysis: each conference-year is reduced to a single summary over its
authors, so year acts as a blocking factor and we avoid treating thousands of
correlated author rows as independent observations. Two summaries are computed:
  - median: robust to skew; the primary aggregate for degree / clustering.
  - mean:   the only informative aggregate for betweenness, whose median is
            pinned at 0 (a majority of authors sit on no shortest paths).
Tests are run for both aggregates so each metric can be read from the summary
that actually carries signal.

Tests performed (all nonparametric, since the metrics are heavy-tailed / floored at 0):

  Between conferences
    - Friedman test (primary) on common years 2017-2025, blocking on year,
      + Nemenyi post-hoc + Kendall's W effect size.
    - Kruskal-Wallis (robustness) on all available years,
      + Dunn's post-hoc (Holm-adjusted) + epsilon-squared effect size.

  Over time (per conference)
    - Mann-Kendall monotonic trend test + Sen's slope.
    - Spearman rank correlation (metric vs. year) as a cross-check.

  Multiple-comparison control
    - Holm-Bonferroni applied within each omnibus family (raw + adjusted p reported).

Run from the repo root:  python analysis/analyze_statistical_significance.py
"""

import os
import itertools
import numpy as np
import pandas as pd
from scipy import stats
import scikit_posthocs as sp
import pymannkendall as mk

CONFERENCES = ["icse", "icsa", "ecsa"]
YEARS = list(range(2015, 2026))
METRICS = ["degree_weighted", "betweenness_weighted", "clustering_weighted"]
AGGREGATES = ["median", "mean"]

METRICS_DIR = "./analysis/metrics"
RESULTS_CSV = "./analysis/statistical_tests_results.csv"

ALPHA = 0.05


def load_aggregates():
    """Reduce every conference-year CSV to the median and mean of each metric.

    Returns a tidy DataFrame with columns: conference, year, and
    <metric>_<aggregate> for each metric/aggregate. Missing conference-years
    are skipped (e.g. ICSA has no 2015/2016 file).
    """
    rows = []
    for conf in CONFERENCES:
        for year in YEARS:
            path = f"{METRICS_DIR}/{conf}_{year}_author_metrics.csv"
            try:
                df = pd.read_csv(path)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue

            row = {"conference": conf, "year": year}
            for m in METRICS:
                row[f"{m}_median"] = df[m].median()
                row[f"{m}_mean"] = df[m].mean()
            rows.append(row)

    return pd.DataFrame(rows).sort_values(["conference", "year"]).reset_index(drop=True)


def holm_adjust(pvalues):
    """Holm-Bonferroni step-down adjustment. Returns adjusted p-values in the
    original order, each capped at 1.0."""
    pvalues = np.asarray(pvalues, dtype=float)
    n = len(pvalues)
    order = np.argsort(pvalues)
    adjusted = np.empty(n, dtype=float)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = (n - rank) * pvalues[idx]
        running_max = max(running_max, val)
        adjusted[idx] = min(running_max, 1.0)
    return adjusted


def verdict(p):
    return "significant" if p < ALPHA else "not significant"


def _is_constant(arrays):
    """True if the pooled values have no variation (tests are undefined)."""
    pooled = np.concatenate([np.asarray(a, dtype=float) for a in arrays])
    return np.unique(pooled).size <= 1


def between_conference_tests(agg):
    """Friedman (+ Nemenyi, Kendall's W) and Kruskal-Wallis (+ Dunn's,
    epsilon-squared) for each metric x aggregate. Returns (results, nemenyi, dunn)."""
    results = []
    nemenyi_tables = {}
    dunn_tables = {}

    for metric in METRICS:
        for aggregate in AGGREGATES:
            col = f"{metric}_{aggregate}"
            # year x conference table of the chosen aggregate
            pivot = agg.pivot(index="year", columns="conference", values=col)

            # ---- Friedman: needs complete blocks (years where all 3 confs exist) ----
            complete = pivot.dropna(axis=0, how="any")[CONFERENCES]
            n_blocks, k = complete.shape
            block_cols = [complete[c].values for c in CONFERENCES]
            if _is_constant(block_cols):
                friedman_chi2, friedman_p, kendalls_w = np.nan, np.nan, np.nan
            else:
                friedman_chi2, friedman_p = stats.friedmanchisquare(*block_cols)
                kendalls_w = friedman_chi2 / (n_blocks * (k - 1))
                if friedman_p < ALPHA:
                    nm = sp.posthoc_nemenyi_friedman(complete.values)
                    nm.index, nm.columns = CONFERENCES, CONFERENCES
                    nemenyi_tables[(metric, aggregate)] = nm

            # ---- Kruskal-Wallis: all available years per conference ----
            groups = [pivot[c].dropna().values for c in CONFERENCES]
            n_total = sum(len(g) for g in groups)
            if _is_constant(groups):
                kw_h, kw_p, epsilon_sq = np.nan, np.nan, np.nan
            else:
                kw_h, kw_p = stats.kruskal(*groups)
                epsilon_sq = kw_h / (n_total - 1)
                if kw_p < ALPHA:
                    dunn = sp.posthoc_dunn(groups, p_adjust="holm")
                    dunn.index, dunn.columns = CONFERENCES, CONFERENCES
                    dunn_tables[(metric, aggregate)] = dunn

            results.append(
                {
                    "metric": metric,
                    "aggregate": aggregate,
                    "test": "Friedman (blocked on year)",
                    "n": n_blocks,
                    "statistic": friedman_chi2,
                    "raw_p": friedman_p,
                    "effect_size": kendalls_w,
                    "effect_name": "Kendall's W",
                }
            )
            results.append(
                {
                    "metric": metric,
                    "aggregate": aggregate,
                    "test": "Kruskal-Wallis (all years)",
                    "n": n_total,
                    "statistic": kw_h,
                    "raw_p": kw_p,
                    "effect_size": epsilon_sq,
                    "effect_name": "epsilon-squared",
                }
            )

    results = pd.DataFrame(results)
    # Holm-adjust within each test family (ignoring undefined / NaN p-values)
    for test_name in results["test"].unique():
        mask = (results["test"] == test_name) & results["raw_p"].notna()
        results.loc[mask, "adj_p"] = holm_adjust(results.loc[mask, "raw_p"].values)
    results["verdict"] = results["adj_p"].apply(
        lambda p: verdict(p) if pd.notna(p) else "undefined (constant input)"
    )

    return results, nemenyi_tables, dunn_tables


def time_trend_tests(agg):
    """Mann-Kendall + Sen's slope + Spearman for each conference x metric x aggregate."""
    results = []
    for metric in METRICS:
        for aggregate in AGGREGATES:
            col = f"{metric}_{aggregate}"
            for conf in CONFERENCES:
                sub = agg[agg["conference"] == conf].sort_values("year")
                mask = sub[col].notna()
                series = sub.loc[mask, col].values
                years = sub.loc[mask, "year"].values

                mk_res = mk.original_test(series)
                if np.unique(series).size <= 1:
                    rho, sp_p = np.nan, np.nan  # Spearman undefined for constant input
                else:
                    rho, sp_p = stats.spearmanr(years, series)
                results.append(
                    {
                        "metric": metric,
                        "aggregate": aggregate,
                        "conference": conf,
                        "n": len(series),
                        "mk_trend": mk_res.trend,
                        "mk_raw_p": mk_res.p,
                        "sens_slope_per_year": mk_res.slope,
                        "spearman_rho": rho,
                        "spearman_p": sp_p,
                    }
                )

    results = pd.DataFrame(results)
    # Holm-adjust the Mann-Kendall family (3 metrics x 2 aggregates x 3 conferences)
    results["mk_adj_p"] = holm_adjust(results["mk_raw_p"].values)
    results["mk_verdict"] = results["mk_adj_p"].apply(verdict)
    return results


def flatten_posthoc(tables, test_name):
    """Turn {(metric, aggregate): 3x3 p-value matrix} into long-form pairwise
    rows: one row per conference pair, with the adjusted pairwise p and verdict.
    The post-hoc p-values are already adjusted for the joint comparison (Nemenyi
    inherently; Dunn via Holm), so they are stored in adj_p."""
    rows = []
    for (metric, aggregate), tbl in tables.items():
        for a, b in itertools.combinations(CONFERENCES, 2):
            p = tbl.loc[a, b]
            rows.append(
                {
                    "metric": metric,
                    "aggregate": aggregate,
                    "test": test_name,
                    "family": "post_hoc",
                    "pair": f"{a} vs {b}",
                    "conf_a": a,
                    "conf_b": b,
                    "adj_p": p,
                    "verdict": verdict(p),
                }
            )
    return pd.DataFrame(rows)


def _fmt(df):
    return df.to_string(index=True, float_format=lambda x: f"{x:.4g}")


def main():
    agg = load_aggregates()

    print("=" * 78)
    print("AGGREGATED MEDIANS PER CONFERENCE-YEAR")
    print("=" * 78)
    print(_fmt(agg))
    coverage = agg.groupby("conference")["year"].agg(["min", "max", "count"])
    print("\nYear coverage per conference:")
    print(_fmt(coverage))

    between, nemenyi_tables, dunn_tables = between_conference_tests(agg)
    trends = time_trend_tests(agg)

    print("\n" + "=" * 78)
    print("BETWEEN-CONFERENCE DIFFERENCES")
    print("=" * 78)
    print(_fmt(between[
        ["metric", "aggregate", "test", "n", "statistic", "raw_p", "adj_p",
         "effect_size", "effect_name", "verdict"]
    ]))

    if nemenyi_tables:
        print("\n-- Nemenyi post-hoc (pairwise p-values; Friedman was significant) --")
        for (metric, aggregate), tbl in nemenyi_tables.items():
            print(f"\n[{metric} ({aggregate})]")
            print(_fmt(tbl))

    if dunn_tables:
        print("\n-- Dunn's post-hoc (Holm-adjusted; Kruskal-Wallis was significant) --")
        for (metric, aggregate), tbl in dunn_tables.items():
            print(f"\n[{metric} ({aggregate})]")
            print(_fmt(tbl))

    # Long-form pairwise post-hoc rows (which conference pairs differ).
    posthoc = pd.concat(
        [
            flatten_posthoc(nemenyi_tables, "Nemenyi (post-hoc Friedman)"),
            flatten_posthoc(dunn_tables, "Dunn (post-hoc KW, Holm)"),
        ],
        ignore_index=True,
    )
    if not posthoc.empty:
        print("\n-- Pairwise post-hoc summary (which conferences differ) --")
        print(_fmt(posthoc[
            ["metric", "aggregate", "test", "pair", "adj_p", "verdict"]
        ]))

    print("\n" + "=" * 78)
    print("TRENDS OVER TIME (per conference)")
    print("=" * 78)
    print(_fmt(trends[
        ["metric", "aggregate", "conference", "n", "mk_trend", "mk_raw_p",
         "mk_adj_p", "mk_verdict", "sens_slope_per_year", "spearman_rho",
         "spearman_p"]
    ]))

    # Persist a flat results table (both test families stacked).
    between_out = between.assign(family="between_conference")
    trends_out = trends.rename(
        columns={
            "mk_trend": "trend",
            "mk_raw_p": "raw_p",
            "mk_adj_p": "adj_p",
            "mk_verdict": "verdict",
            "sens_slope_per_year": "effect_size",
        }
    ).assign(test="Mann-Kendall", effect_name="Sen's slope/yr", family="time_trend")
    combined = pd.concat(
        [between_out, trends_out, posthoc], ignore_index=True, sort=False
    )

    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    combined.to_csv(RESULTS_CSV, index=False)
    print(f"\nResults written to {RESULTS_CSV}")


if __name__ == "__main__":
    main()
