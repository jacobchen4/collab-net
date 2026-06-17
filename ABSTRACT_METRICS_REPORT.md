# Abstract Network Metrics — Methods & Results Outline

All figures are in `analysis/plots/`. All tables are in `analysis/abstract_metrics/`.

---

## Methods

### Network representation
The co-authorship graph G is a weighted undirected graph where nodes are authors
and edges carry `weight` = number of shared publications and `distance` = 1/weight.
The full graph contains 13,903 nodes and 45,405 edges. Per-(conference, year)
subgraphs (29 non-empty partitions across ICSA, ECSA, ICSE × 2016–2025) were
constructed from the same Neo4j database and stored as separate NetworkX pickles.

### Task 5 — Degree distribution fit
Degrees were fitted to a power law using maximum-likelihood estimation via the
`powerlaw` package (Alstott et al., 2014). x_min was selected by minimising the
KS statistic. A log-likelihood ratio test against a log-normal alternative was
used to select the better-fitting model.

### Task 6 — Small-world coefficient
Metrics σ (Watts & Strogatz, 1998) and ω (Humphries & Gurney, 2008) were
computed on the giant connected component (10,307 nodes). Average shortest path
length L was computed via exact BFS from every node (~122 s). The Erdős–Rényi
random-graph baselines used C_rand ≈ ⟨k⟩/n and L_rand ≈ ln(n)/ln(⟨k⟩).

### Task 7 — Degree assortativity
Newman's degree assortativity coefficient r was computed for the full graph and
for all 29 (conf, year) subgraphs using `nx.degree_assortativity_coefficient`.

### Task 8 — Temporal role transitions
For each subgraph, authors were classified into five structural roles
(broker, hub, embedded, peripheral, core) using per-snapshot 25th/75th percentile
thresholds on betweenness, degree, and clustering — ensuring roles are relative to
that year's network. For each author appearing in two consecutive years at the same
conference, the role pair (role_t → role_{t+1}) was recorded and aggregated into a
5×5 transition probability matrix.

### Task 9 — Community persistence
Communities were detected in each subgraph using the Louvain algorithm (seed = 42).
For each consecutive year pair, every community C_i in year t was matched to its
closest community in year t+1 by maximising the Jaccard similarity
J(C_i, D_j) = |C_i ∩ D_j| / |C_i ∪ D_j|. The mean best-match Jaccard across all
communities in year t serves as the persistence score for that transition.

### Task 10 — Cross-pollination
For each year, the set of author names in each ICSA and ECSA subgraph was
intersected with the ICSE author set for the same year. Cross-pollination is
reported as the fraction of architecture-conference authors who also published at
ICSE that year.

### Task 11 — K-shell decomposition
The k-core number of every node was computed on the full graph using
`nx.core_number`. K-shell index (= k-core number) provides a parameter-free
topological depth measure: a node belongs to k-shell s if it is in the s-core
but not the (s+1)-core.

### Task 12 — Retention analysis
Using the 29 subgraph metrics CSVs, each author's debut year and presence set
were recorded per conference. For each debut cohort Y, the retention rate at lag t
is the fraction of cohort members who also appeared in year Y+t. Rates were
averaged across cohorts, weighted by cohort size.

---

## Results

### Task 5 — Degree distribution is log-normal, not scale-free
*(See `analysis/plots/task5_degree_powerlaw.png`)*

- Fitted power-law exponent α = 2.70, x_min = 7, KS distance D = 0.025.
- Log-likelihood ratio vs. log-normal: R = −23.25 (p < 0.0001).
- **The log-normal is the significantly better fit.** The degree distribution is
  heavy-tailed but does not follow a pure power law. This suggests the network
  grows through a combination of preferential attachment and bounded growth
  processes (e.g., finite research-group sizes), consistent with prior findings in
  co-authorship networks (Newman, 2001).

### Task 6 — Strongly small-world structure
- Giant component: n = 10,307, m = 39,473, ⟨k⟩ = 7.66.
- Clustering coefficient C = 0.806 vs. random-graph baseline C_rand = 0.00074
  (ratio ≈ 1,086×).
- Average path length L = 5.88 vs. L_rand = 4.54 (only 30% longer than random).
- Small-world coefficient **σ = 836.7** (>> 1); ω = −1,083.3.
- **The network is strongly small-world**: authors are embedded in extremely dense
  local cliques yet are globally reachable within ~6 hops on average. The dominant
  driver is the very high clustering, not path-length elongation.

### Task 7 — Full graph is mildly assortative; subgraphs are disassortative
*(See `analysis/plots/task7_assortativity_trends.png`)*

- Full-graph r = **+0.129** (mildly assortative): high-degree authors show some
  tendency to cluster together globally.
- All per-(conf, year) subgraphs are **strongly disassortative**:
  - ICSA: mean r = −0.403 (range −0.499 to −0.307)
  - ECSA: mean r = −0.453 (range −0.519 to −0.351)
  - ICSE: mean r = −0.208 (range −0.251 to −0.158)
- The sign reversal between full and subgraph assortativity is a Simpson's
  paradox-type effect: within any single conference-year, high-degree authors
  (brokers) disproportionately connect to low-degree newcomers. The positive global
  signal emerges from cross-conference aggregation of large, densely-connected hubs.
- Architecture conferences (ICSA, ECSA) are more disassortative than ICSE,
  implying that brokerage activity — connecting periphery to centre — is a stronger
  structural feature in the smaller venues.

### Task 8 — Core is the most stable role; hub and embedded are transient
*(See `analysis/plots/task8_transition_heatmap.png` and `task8_role_proportions.png`)*
*(See `analysis/abstract_metrics/task8_transition_matrix.csv`)*

- 4,076 consecutive-year transitions recorded across all author-conference pairs.
- Self-transition (stability) rates:
  | Role       | P(same role next year) |
  |------------|------------------------|
  | core       | **69.0%** — most stable |
  | broker     | **50.1%** — moderately stable |
  | peripheral | 26.1% |
  | hub        | 0% — effectively transient |
  | embedded   | 0% — effectively transient |
- **Core is the dominant absorbing state**: most role transitions converge toward
  core over multiple years.
- Hub and embedded are not stable structural positions; authors classified into these
  roles almost always transition to a different role the following year. This may
  reflect sensitivity of the threshold-based classifier for these boundary roles,
  or genuine structural fluidity at the boundary of hub and embedded classification.
- Brokers show ~50% year-over-year persistence, indicating that brokerage is a
  semi-stable property requiring sustained effort to maintain.

### Task 9 — Research communities are fluid (Jaccard < 0.35 universally)
*(See `analysis/plots/task9_community_persistence.png`)*

- Mean best-match Jaccard scores across all conference-year pairs ranged from 0.12
  to 0.35. No transition exceeded 0.36.
- ECSA showed the highest single-transition persistence (2017→2018: J = 0.35;
  2024→2025: J = 0.30), consistent with a tighter, more specialised community.
- ICSE showed the lowest persistence overall (mean J ≈ 0.18), reflecting its
  larger, more diverse author pool.
- **Community membership turns over substantially every year.** Less than 35% of
  any community's members consistently appear in the same cluster in the following
  year. This implies that co-authorship clusters in SE conferences reorganise
  continuously rather than persisting as stable research groups.

### Task 10 — Cross-pollination peaked 2016–2020 and collapsed post-2021
*(See `analysis/plots/task10_cross_pollination.png`)*

- 2016–2020: 12–23% of ICSA/ECSA authors also published at ICSE annually.
- 2021–2023: sharp decline to 2–6%, coinciding with COVID-19-era disruptions to
  in-person conference attendance (virtual formats may have changed submission
  patterns).
- 2024 partial recovery: both ICSA and ECSA returned to ~10%.
- ICSA cross-pollination with ICSE was consistently higher than ECSA's before 2021,
  suggesting ICSA attracts more researchers with broad SE publication portfolios.
- **The architecture and general-SE communities became more siloed post-pandemic.**

### Task 11 — The k=37 nucleus contains 76 densely interconnected authors
*(See `analysis/plots/task11_kshell_histogram.png` and `task11_kshell_by_role.png`)*
*(See `analysis/abstract_metrics/task11_author_kshell.csv`)*

- Max k-shell: **k = 37**. The k-37 nucleus contains 76 authors, all of whom have
  ≥ 37 mutual co-authorship connections within the core.
- The k-shell histogram is heavily right-skewed: the vast majority of authors have
  k-shell ≤ 5, consistent with the log-normal degree distribution.
- By role, brokers occupy the highest median k-shell (as expected — high-betweenness
  nodes are deeply embedded), followed by core, hub, embedded, and peripheral.
- Top k-37 authors by betweenness include Neha Rungta, Emina Torlak, Peng Di, and
  Zhaogui Xu — predominantly software analysis / verification researchers, suggesting
  the densest nucleus of the graph is anchored by a formal-methods sub-community.
- K-shell provides a finer, parameter-free depth hierarchy complementary to the
  role taxonomy: while all 76 k-37 authors are classified as core or broker, k-shell
  distinguishes further gradations of structural embeddedness within those roles.

### Task 12 — Author retention is uniformly low; ICSE retains slightly better
*(See `analysis/plots/task12_retention_curves.png`)*
*(See `analysis/abstract_metrics/task12_author_cohorts.csv`)*

- 1-year retention rates: ICSE 14.7%, ICSA 11.6%, ECSA 11.7%.
- 3-year retention: ICSE 10.8%, ECSA 6.7%, ICSA 5.7%.
- 5-year retention: ICSE 7.8%, ECSA 6.6%, ICSA 8.4%.
- **The overwhelming majority of authors are one-time or infrequent contributors.**
  Even at the 1-year lag, ~85–88% of debut authors do not return the following year.
- ICSE retains authors at a modestly higher rate than the architecture venues at
  all lags, likely reflecting its larger community offering more collaboration
  opportunities and its broader topical scope attracting recurring contributors.
- The low retention rates corroborate the high community-churn seen in Task 9:
  communities reorganise because a large fraction of their members do not return.
