# Analysis

Scripts for computing author-level network metrics from the Neo4j Aura coauthorship graph and exporting to CSV.

---

## Setup

1. Install dependencies from the repo root:
   ```
   pip install -r requirements.txt
   ```

2. Copy the credential template and fill in your Aura details:
   ```
   copy analysis\config.yaml.template analysis\config.yaml
   ```
   `config.yaml` is gitignored — never commit it.

---

## Pipeline

Run all scripts from the **repo root**. Steps 1–3 must run in order; steps 4–6 are independent and can run in any order after step 3.

### Step 1 — Fetch the graph from Neo4j
```
python analysis/fetch_graph.py
```
Queries the database and saves two networkx graph files locally:
- `analysis/multigraph.pkl` — raw MultiGraph (one edge per shared paper)
- `analysis/graph.pkl` — collapsed weighted Graph (one edge per coauthor pair, `weight` = # shared papers, `distance` = `1/weight`)

### Step 2 — Compute core metrics
```
python analysis/compute_metrics.py
```
Writes `analysis/author_metrics.csv` with degree, betweenness, and connected component columns.

> **Runtime:** Exact betweenness on ~14k nodes takes ~50 minutes. For faster approximate results:
> ```
> python analysis/compute_metrics.py --approx 500
> ```

### Step 3 — Add clustering coefficients
```
python analysis/add_clustering.py
```
Appends `clustering_unweighted` and `clustering_weighted` columns to `author_metrics.csv` in place. Fast (seconds).

### Step 4 — Classify structural roles
```
python analysis/classify_roles.py
```
Writes `analysis/author_roles.csv` — all metrics plus a `role` column.

### Step 5 — Detect research communities
```
python analysis/detect_communities.py
```
Runs Louvain community detection on the weighted graph. Writes `analysis/author_communities.csv`.

### Step 6 — Find cross-conference bridge authors
```
python analysis/bridge_authors.py
```
Identifies authors who published in 2+ conferences. Writes `analysis/bridge_authors.csv`.

---

## Outputs

### `author_metrics.csv`
One row per author (13,903 rows).

| Column | Description |
|---|---|
| `name` | Author name as stored in the database |
| `database_id` | Neo4j `elementId` — stable string identifier for the `:author` node |
| `degree_weighted` | Number of unique coauthors (degree on collapsed graph) |
| `degree_total` | Total coauthorship edges, counting each shared paper separately |
| `betweenness_weighted` | Betweenness on collapsed graph; edge distance = `1/weight` |
| `betweenness_unweighted` | Betweenness on collapsed graph; all edges distance = 1 |
| `clustering_unweighted` | Fraction of an author's coauthors who also collaborated with each other |
| `clustering_weighted` | Clustering weighted by number of shared papers |
| `connected_component` | Integer component ID — `0` is the largest component, ascending by size |

### `author_roles.csv`
All columns from `author_metrics.csv` plus:

| Column | Description |
|---|---|
| `role` | Structural role: `broker`, `hub`, `embedded`, `peripheral`, or `core` |

Role definitions (applied in priority order, using 25th/75th percentile thresholds):

| Role | Condition |
|---|---|
| `broker` | Betweenness ≥ 75th percentile **and** clustering < 50th percentile |
| `hub` | Degree ≥ 75th percentile **and** clustering < 50th percentile |
| `embedded` | Clustering ≥ 75th percentile **and** betweenness < 50th percentile |
| `peripheral` | Degree < 25th percentile |
| `core` | All others |

### `author_communities.csv`
One row per author. Louvain communities sorted descending by size (`community_id = 0` is largest).

| Column | Description |
|---|---|
| `name` | Author name |
| `database_id` | Neo4j `elementId` |
| `community_id` | Community index (0 = largest) |
| `community_size` | Number of authors in that community |

### `bridge_authors.csv`
One row per author who published in 2+ conferences, sorted by conference count then betweenness.

| Column | Description |
|---|---|
| `name` | Author name |
| `n_conferences` | Number of distinct conferences published in |
| `ICSA` / `ICSE` / `ECSA` | Publication count per conference |
| `total_pubs` | Total publications across all conferences |
| + network metrics | `degree_weighted`, `betweenness_unweighted/weighted`, `clustering_unweighted`, `connected_component` |

---

## Key numbers (as of 2026-06-07)

| Metric | Value |
|---|---|
| Total authors | 13,903 |
| Total publications | 7,553 |
| Conferences | ICSA, ICSE, ECSA (2016–2025) |
| Unique coauthor pairs | 45,405 |
| Raw coauthorship edges | 56,589 |
| Connected components | 1,120 |
| Largest component | 10,307 authors (74%) |
| Louvain communities | 1,176 |
| Largest community | 632 authors |
| Bridge authors (2+ conferences) | 844 |
| Bridge authors (all 3 conferences) | 212 |

---

## Data source

The underlying graph was loaded into Neo4j from `csvs/author_publications.csv` (extracted from the DBLP XML dump) after author disambiguation. See `database_load/` for the loading scripts and `disambiguation/` for the disambiguation pipeline.

## Statistical Tests

### Friedman test

#### between-conference, primary

It's the nonparametric equivalent of a repeated-measures ANOVA. You picked "year as a blocking factor," and Friedman is built exactly for that: it ranks the three conferences within each year and asks whether one conference consistently ranks higher across years. Using within-year ranks cancels out year-to-year swings (e.g. a big-program year) that would otherwise add noise, and it makes no normality assumption — which matters because the metrics are skewed.

### Nemenyi

#### post-hoc — follow-up to Friedman

Friedman only says "the conferences differ somewhere." Nemenyi is the matched post-hoc that tells you which pairs (ICSE vs ICSA, ICSE vs ECSA, ICSA vs ECSA) differ, while correcting for the fact that you're making three comparisons at once.

### Kruskal–Wallis + Dunn's

#### between-conference, robustness check

Friedman on 9 blocks has low power, and it forces you to drop ICSA's missing 2016–17 to keep complete blocks. Kruskal–Wallis treats the yearly aggregates as independent samples, so it can use all available years per conference. If both KW and Friedman agree, the conclusion is solid; if they disagree, that disagreement is itself informative. Dunn's is the correct pairwise post-hoc after KW (same role Nemenyi plays for Friedman).

### Mann–Kendall

#### trend test — time trends, primary

It tests for a monotonic trend (steady rise or fall) without assuming the trend is linear or the data normal — ideal for short, noisy time series. It answers "is this metric drifting up or down over the decade?" per conference.

### Sen's slope

#### trend magnitude

Mann–Kendall only gives direction + significance; Sen's slope is the robust (outlier-resistant) estimate of how much per year, so you can report the size of the change, not just its existence.

### Spearman correlation

#### trend cross-check

A simple rank correlation of metric-vs-year. It corroborates Mann–Kendall's direction/strength using a different mechanism; agreement between the two adds confidence.

### Holm–Bonferroni correction

#### not a test, a guardrail

You're running many tests across 3 metrics; some will look "significant" by pure chance. Holm adjusts the p-values to control that family-wise error, so you don't over-claim.

### Effect sizes

#### (Kendall's W, epsilon-squared, Sen's slope)

with this data, p-values can be driven by quirks of small samples or, conversely, hide trivially-small-but-real differences. Effect sizes report the magnitude so "significant" doesn't get confused with "important."

---

One theme tying it all together: every test is nonparametric / rank-based because the metrics are heavy-tailed and floored at zero, which rules out the usual ANOVA/t-test family.