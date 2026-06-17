# Discussion

## Network scale and centrality (Task 1)

The full co-authorship graph spans 13,903 authors and 45,405 edges. Centrality
statistics reveal a highly skewed network: the median weighted degree is 4,
meaning the typical author co-authored with just four distinct collaborators,
yet the maximum is 176 (Yan Liu). The median clustering coefficient of 1.0
indicates that more than half of all authors are embedded in perfectly closed
triangles — every pair of their co-authors has also co-authored with each other —
reflecting the tight group structure of academic research teams.

Betweenness centrality is zero for the median author, but a handful of structural
bridges carry a disproportionate share of shortest paths. Rick Kazman ranks
higher in betweenness than several authors with greater publication volume,
confirming that *structural position* and *productivity* are distinct properties:
a moderately prolific author who bridges otherwise separate communities provides
more global connectivity than a very prolific author who publishes entirely within
one tight cluster.

The 1,120 connected components, with 74.1% of authors in a single giant component,
indicate that the collaboration network is globally cohesive but not fully
connected. The remaining 25.9% belong to isolated clusters — small research groups
that have not yet bridged into the main community.

---

## Role composition (Task 2)

Three structural roles emerge: core (61.9%), broker (25.0%), and peripheral (13.1%).
The absence of hub and embedded roles is a network-specific finding: this dataset's
degree and clustering distributions do not simultaneously produce authors meeting
both the high-degree/low-clustering threshold (hub) or the high-clustering/
low-betweenness threshold (embedded) at the 75th/25th percentile cutoffs.

The dominance of core reflects that most SE conference authors are well-integrated
into local research groups without being structural bridges or highly marginal.
Brokers (25%) are a substantial minority — median degree 8 and non-zero betweenness
— suggesting they actively span multiple research subfields. The peripheral 13%
(median degree 2, zero betweenness) are one-time or marginal contributors who
attended a conference with one or two collaborators but have not embedded further
into the network.

---

## Community structure (Task 3)

The 1,176 Louvain communities exhibit extreme size inequality: median size 3,
mean 11.8, max 632. Nearly 30% of communities are singletons — isolated authors
or disconnected pairs. This bimodal structure arises naturally from the
heavy-tailed degree distribution: prolific, well-connected authors nucleate large
communities while peripheral authors form isolated dyads.

The top 10 communities containing 29.7% of all authors implies significant
concentration of the network's "community mass" in a small number of large
research clusters. These likely correspond to stable, long-running research groups
or topical subcommunities (e.g., formal methods, software architecture patterns,
empirical SE). The roughly power-law community-size distribution is consistent
with findings in other academic co-authorship networks.

---

## Cross-conference bridges (Task 4)

Bridge authors — those publishing at more than one of the three venues — are rare
(844 out of 13,903, or 6.1%) but structurally critical. The two highest-betweenness
authors in the entire network (Yan Liu at 0.037 and David Lo at 0.035) are both
2-conference bridges spanning ICSA and ICSE, not the most prolific 3-conference
authors. This confirms that betweenness reflects *topological position*, not
publication volume: these authors derive their centrality from sitting on the
shortest paths connecting the ICSA and ICSE sub-communities, not from sheer output.

ICSA–ICSE bridges (245) outnumber ECSA–ICSE bridges (206), consistent with
ICSA's historically closer relationship to mainstream SE research. The weak
correlation between total publications and betweenness (Task 4 scatter plot) is
a direct consequence of the small-world structure from Task 6: once the giant
component is densely connected, betweenness accrues to bottleneck positions, not
to volume of activity.

---

## Degree distribution (Task 5)

The degree distribution is heavy-tailed but log-normal rather than a power law
(LR test: R = −23.25, p < 0.0001). A pure power law (Barabási–Albert preferential
attachment) predicts an unbounded "rich get richer" dynamic. The log-normal fit
instead implies growth governed by preferential attachment *combined with*
multiplicative constraints — finite research group sizes, conference paper limits,
career durations — that impose an upper bound on degree accumulation. This is
consistent with Newman's (2001) findings in other academic co-authorship networks
and suggests that while well-connected authors disproportionately attract new
co-authors, the effect saturates rather than producing scale-free hubs.

---

## Small-world structure (Task 6)

With σ = 836.7 and ω = −1,083.3, the network is strongly small-world. The
clustering coefficient C = 0.806 is 1,086× higher than the random-graph baseline,
while the average path length L = 5.88 is only 30% longer than random (L_rand =
4.54). This asymmetry — enormous local clustering, near-random global path length
— is the canonical small-world signature.

The dominant driver is clustering, not path elongation. Authors are embedded in
extremely tight research cliques (co-author groups where nearly everyone has
worked with everyone else), yet any two researchers in the giant component are on
average fewer than six hops apart. The practical implication is that methods,
ideas, and collaborations can diffuse across the SE research community quickly,
even though most authors work almost exclusively within their local group.

---

## Degree assortativity (Task 7)

The sign reversal between the full-graph assortativity (r = +0.129) and
per-conference-year assortativity (r ranging from −0.208 to −0.453) is a
Simpson's paradox-type effect.

Within any single conference-year, high-degree authors disproportionately connect
to low-degree newcomers — brokers recruit peripheral authors, which drives negative
local assortativity. Across the full graph, however, the aggregation of large,
densely interconnected hubs who span multiple conferences and years produces an
apparent positive degree–degree correlation. The global "assortative" signal is
therefore an artifact of cross-conference hub concentration, not a genuine
within-community phenomenon.

The architecture venues (ICSA, ECSA) are more disassortative than ICSE (mean r ≈
−0.43 vs. −0.21), consistent with their smaller size: in a compact venue the few
high-degree authors must connect extensively to the periphery simply because there
are fewer potential high-degree peers available.

---

## Community persistence (Task 9)

Mean best-match Jaccard scores between consecutive-year community partitions
ranged from 0.12 to 0.35 across all conferences, with no single transition
exceeding 0.36. These values indicate substantial community turnover every year:
fewer than 35% of a community's members consistently cluster together in the
following year. Community membership is not a stable structural property — it
reflects the publication composition of a given year rather than persistent
research groups.

ECSA shows slightly higher persistence (max J = 0.35) than ICSE (mean J ≈ 0.18),
consistent with ECSA's smaller, more specialised author pool. When a venue is
small and topically focused, the same authors recur year over year and tend to
co-author with the same peers, yielding more stable community structure. ICSE's
lower persistence reflects its larger, more diverse population.

Taken together with Task 3, the picture is one of a few stable mega-communities
(large, topically dense subfields) surrounded by a sea of ephemeral small clusters
that reorganise annually as authors enter, exit, or shift their collaboration
patterns.

---

## K-shell decomposition (Task 11)

The k-shell analysis reveals deep hierarchical structure within the network. The
k-37 nucleus — 76 authors, each with at least 37 mutual connections within the
nucleus — represents extreme structural embeddedness. The histogram is heavily
right-skewed: most authors have k-shell ≤ 5, consistent with the log-normal
degree distribution and the high proportion of peripheral and single-visit authors.

The nuclear authors are dominated by software analysis and formal methods
researchers (Neha Rungta, Emina Torlak, Peng Di, Zhaogui Xu), suggesting that
the densest, most mutually interconnected subfield is formal verification and
program analysis — a research area characterised by long-running group
collaborations and a relatively small international community.

K-shell complements the role taxonomy from Task 2: all 76 k-37 authors are
classified as core or broker by the percentile-based classifier, but k-shell
distinguishes further gradations of structural depth within those roles. A broker
at k-shell 37 is fundamentally different from a broker at k-shell 2, even though
both satisfy the same betweenness/clustering threshold conditions. Using both
measures together provides a richer characterisation of author position in the
network.
