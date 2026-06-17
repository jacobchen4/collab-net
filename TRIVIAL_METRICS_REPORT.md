# Descriptive Network Metrics — Methods & Results Outline

All figures are in `analysis/plots/`.

---

## Methods

### Network representation
The co-authorship graph contains 13,903 authors (nodes) and 45,405 weighted edges.
Edge weight equals the number of shared publications between two authors.
Per-author centrality metrics, structural roles, Louvain community assignments,
and cross-conference bridge membership were pre-computed by the upstream pipeline
and stored in four CSV files in `analysis/`.

### Task 1 — Author centrality summary
Three centrality metrics were summarised across all 13,903 authors from
`author_metrics.csv`: weighted degree (sum of co-authorship edge weights),
unweighted betweenness centrality (fraction of all-pairs shortest paths passing
through the node), and unweighted local clustering coefficient. Top-10 authors
were ranked by each metric to identify the network's most prominent collaborators
and structural bridges.

### Task 2 — Structural role distribution
Author roles were read directly from `author_roles.csv`, which was produced by
`classify_roles.py` using per-graph 25th/75th percentile thresholds on betweenness,
degree, and clustering. The three roles present in this dataset are:

- **peripheral** — low degree; weakly connected authors
- **core** — mid-range on all three metrics; typical well-connected authors
- **broker** — high betweenness relative to low clustering; structural bridges

Role counts, proportions, and per-role median centrality values were computed.
A boxplot compared degree and betweenness distributions across roles (outliers
excluded for readability).

### Task 3 — Community size distribution
Louvain community assignments were read from `author_communities.csv`.
The per-community size distribution was computed by grouping authors by
`community_id`. A log–log histogram was used to capture the wide dynamic range
from singleton communities (size 1) to the largest community (size 632).

### Task 4 — Cross-conference bridge authors
`bridge_authors.csv` lists the 844 authors who published at more than one of the
three conferences (ICSA, ECSA, ICSE) between 2016–2025. Bridge authors were
stratified by the number of distinct conferences attended (2 or 3) and by
conference pair for 2-conference bridges. Top-10 bridges were identified by total
publication count and by full-graph betweenness centrality.

---

## Results

### Task 1 — Highly skewed centrality; a small elite dominates
*(See `analysis/plots/task1_degree_histogram.png`)*

- **Weighted degree**: mean = 6.5, median = 4.0, max = 176 (Yan Liu).
  The histogram shows a pronounced right tail — the vast majority of authors have
  degree ≤ 10, while a small elite exceeds 50.
- **Betweenness**: mean = 0.00019, median = 0.0 (most authors lie on no shortest
  path), max = 0.037 (Yan Liu). The top betweenness authors are not identical to
  the top degree authors: Rick Kazman (degree 71) ranks 3rd in betweenness ahead of
  authors with far higher degree, indicating that structural bridging and raw
  collaboration volume are distinct roles.
- **Clustering**: mean = 0.784, median = 1.0. The median of 1.0 means more than
  half of all authors are in perfectly closed triangles — consistent with the
  strongly small-world result (Task 6 of the abstract metrics).
- **Connected components**: 1,120 total; the giant component contains 10,307 authors
  (74.1% of all authors). The remaining 1,119 components are small isolated groups.

### Task 2 — Core is the dominant role; brokers are a structurally distinct quarter
*(See `analysis/plots/task2_role_counts.png` and `task2_role_metrics.png`)*

| Role       | Count | % of authors |
|------------|------:|-------------:|
| core       | 8,608 | 61.9%        |
| broker     | 3,475 | 25.0%        |
| peripheral | 1,820 | 13.1%        |

- **Core** authors form the majority: median degree 5, median betweenness 0, median
  clustering 1.0 — well-connected within tight local cliques but not on many
  cross-community paths.
- **Brokers** have median degree 8 (higher than core) but median clustering 0.23,
  confirming they bridge weakly connected neighbourhoods. Median betweenness (0.0001)
  is non-zero, unlike core and peripheral.
- **Peripheral** authors have median degree 2 and median betweenness 0 — marginal
  contributors typically attached to one or two collaborators.
- Only three roles exist in this network (hub and embedded are absent) because the
  degree and clustering distributions do not simultaneously produce authors meeting
  both the high-degree + low-clustering threshold (hub) or the high-clustering +
  low-betweenness threshold (embedded) at the 75th/25th percentile cutoffs.

### Task 3 — Community structure is highly unequal; most communities are tiny
*(See `analysis/plots/task3_community_sizes.png`)*

- **1,176 communities** detected by Louvain on the full graph.
- Size distribution is extremely skewed: median size = 3, mean = 11.8, max = 632.
- **29.9% of communities are singletons** (352 of 1,176) — isolated authors or
  disconnected pairs that Louvain cannot merge into larger groups.
- The **top 10 communities contain 4,132 authors (29.7%)** of the network. The top
  5 alone account for 17.2% (2,396 authors), indicating that despite the long tail
  of small communities, a small number of mega-communities dominate the structure.
- The log–log histogram shows a roughly power-law community-size distribution,
  consistent with the scale-free-like community structure commonly observed in
  academic co-authorship graphs.

### Task 4 — Bridge authors are rare and disproportionately central
*(See `analysis/plots/task4_bridge_conferences.png` and `task4_bridge_scatter.png`)*

- **844 bridge authors** out of 13,903 total (6.1% of the network).
- **632 (74.9%) span exactly 2 conferences; 212 (25.1%) span all 3.**
- 2-conference pair breakdown:
  - ICSA + ICSE: 245 authors (most common pair)
  - ECSA + ICSE: 206 authors
  - ICSA + ECSA: 181 authors
- ICSA–ICSE bridges outnumber ECSA–ICSE bridges, consistent with ICSA's historically
  closer relationship to mainstream SE research.
- **Top bridges by total publications** are dominated by 3-conference authors:
  Patricia Lago (48 pubs), Rick Kazman (41), Patrizio Pelliccione (37).
  David Lo 0001 (54 pubs) and Yan Liu (53) are the most prolific 2-conference bridges
  (both ICSA + ICSE only).
- **Top bridges by betweenness** are Yan Liu (0.037) and David Lo 0001 (0.035),
  both 2-conference bridges — their structural importance is driven by their role
  as bottlenecks between the ICSA and ICSE communities rather than broad
  multi-venue presence.
- The scatter plot shows weak correlation between total publications and betweenness:
  high-betweenness bridges tend to also have high degree, but many prolific authors
  contribute within tight cliques and therefore have low betweenness.
