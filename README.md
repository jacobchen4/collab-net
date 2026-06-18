# Collaboration Network Analysis

Co-authorship network analysis of three software engineering conferences (ICSE, ICSA, ECSA) from 2016 to 2025, sourced from DBLP.

For a summary of findings, see [documentation/phase_2.md](documentation/phase_2.md).

## Prerequisites

- Python 3.10+
- A Neo4j Aura instance with the co-authorship graph loaded (see [Data Upload](#data-upload) below)

```
pip install -r requirements.txt
```

## Neo4j Connection

Copy the credential template into both directories that need it and fill in your Aura details:

```
copy config.yaml.template analysis\config.yaml
copy config.yaml.template database_load\config.yaml
```

```yaml
credentials:
  uri: 'neo4j+s://738a9212.databases.neo4j.io'
  user: '738a9212'
  password: 'LLdrXoQtv7noKIxLg41vZCb0I9nyuDUnjatXeSEcpxs'
  database: '738a9212'
  instance_id: '738a9212'
  instance_name: 'Co-author Graph'
```

`config.yaml` is gitignored.

## Reproducing Results

All scripts are run from the **repo root**. The pipeline has three phases: data preparation, graph analysis, and statistical analysis. Each phase must complete before the next begins; steps within a phase can run in any order unless noted.

### Phase 1: Data Preparation

These steps build the dataset and load it into Neo4j. If you already have access to a populated Neo4j instance, skip to Phase 2.

#### 1a. Extract publications from DBLP

Download the [DBLP XML dump](https://dblp.org/xml/) and its DTD. Place them as:

```
collab-net/
  dblp.dtd
  dblp.xml/
    dblp.xml
```

```
python extract_dblp.py
```

Produces `csvs/author_publications.csv` (~28k rows).

#### 1b. Disambiguate authors

```
python disambiguation/disambiguate_strict.py
python disambiguation/apply_disambiguation.py
```

The first script identifies author name variants (diacritics, abbreviations, middle names) and writes `csvs/disambiguation_strict.csv`. The second applies confirmed merges to `csvs/author_publications.csv`. See [documentation/phase_1.md](documentation/phase_1.md) for details on the disambiguation process.

#### 1c. Upload to Neo4j

With a fresh Neo4j Aura instance configured:

```python
from database_load.database_load import *

# Creates author nodes, publication nodes, and AUTHORED edges
defineAuthorshipNodesAndEdges()

# Creates COAUTHORED_WITH edges between co-authors on each publication
pubs = getAllPublications()['p']
defineCoauthorshipEdges(pubs)
```

### Phase 2: Graph Analysis

These steps fetch the graph locally, compute metrics, and generate all analysis outputs. **Steps 2a and 2b must run in order.** Steps 2c onward are independent.

#### 2a. Fetch the graph from Neo4j

```
python analysis/fetch_graph.py
```

Saves two NetworkX graph files:
- `analysis/multigraph.pkl` (one edge per shared paper)
- `analysis/graph.pkl` (collapsed; edge weight = shared paper count)

#### 2b. Compute core author metrics

```
python analysis/compute_metrics.py
```

Writes `analysis/author_metrics.csv` with degree, betweenness, clustering, and component columns.

> Exact betweenness on ~14k nodes takes ~50 minutes. For faster approximate results:
> `python analysis/compute_metrics.py --approx 500`

#### 2c. Generate conference-year subgraphs

```
python analysis/generate_subgraphs.py
```

Partitions the graph into 29 conference-year subgraphs, saving graphs to `analysis/graphs/` and per-partition metrics to `analysis/metrics/`. **Required before steps 2g and 2h.**

#### 2d. Classify structural roles

```
python analysis/classify_roles.py
```

Writes `analysis/author_roles.csv` with a `role` column (broker, hub, embedded, peripheral, or core).

#### 2e. Detect communities

```
python analysis/detect_communities.py
```

Runs Louvain community detection. Writes `analysis/author_communities.csv`.

#### 2f. Find bridge authors

```
python analysis/bridge_authors.py
```

Identifies authors publishing in 2+ conferences. Writes `analysis/bridge_authors.csv`.

#### 2g. Compute abstract structural metrics

```
python analysis/compute_abstract_metrics.py
```

Runs eight analysis tasks (power-law test, small-world coefficient, assortativity, role transitions, community persistence, cross-pollination, k-shell decomposition, author retention). Outputs CSVs to `analysis/abstract_metrics/` and plots to `analysis/plots/`. Individual tasks can be run selectively:

```
python analysis/compute_abstract_metrics.py --tasks 5 6 11
```

#### 2h. Statistical significance tests

```
python analysis/analyze_statistical_significance.py
```

Requires `analysis/metrics/` to be populated (step 2c). Writes `csvs/statistical_test_results.csv`.

#### 2i. Generate summary plots

```
python analysis/compute_trivial_metrics.py
```

Produces degree histograms, role distributions, community size plots, and bridge author breakdowns in `analysis/plots/`.

```
python analysis/analyze_author_metrics.py
```

Produces per-conference metric trend plots and optionally an Excel workbook with per-partition statistics.

```
python analysis/analyze_conference_metrics.py
```

Produces author/publication count trends per conference.

### Quick Reference: Execution Order

```
Phase 1 (data prep):          1a -> 1b -> 1c

Phase 2 (analysis):           2a -> 2b -> 2c ─┬─> 2g
                                    │          └─> 2h
                                    ├─> 2d
                                    ├─> 2e
                                    ├─> 2f
                                    └─> 2i
```

## Repository Structure

```
collab-net/
  csvs/                        Source data and result CSVs
    author_publications.csv      Author-publication records (post-disambiguation)
    author_publications.csv.bak  Pre-disambiguation backup
    disambiguation_*.csv         Disambiguation pair files
    statistical_test_results.csv Statistical test outputs

  analysis/                    Graph analysis scripts and outputs
    fetch_graph.py               Fetches graph from Neo4j into local pickles
    compute_metrics.py           Computes per-author network metrics
    generate_subgraphs.py        Builds conference-year subgraphs
    classify_roles.py            Assigns structural roles
    detect_communities.py        Louvain community detection
    bridge_authors.py            Cross-conference bridge author identification
    compute_abstract_metrics.py  Abstract structural metrics (8 tasks)
    compute_trivial_metrics.py   Summary visualizations
    analyze_author_metrics.py    Per-conference author metric trends
    analyze_conference_metrics.py Conference-level publication/author trends
    analyze_statistical_significance.py  Statistical tests on partitions
    connection.py                Neo4j connection utilities
    plots/                       Generated PNG charts
    graphs/                      Conference-year subgraph pickles
    metrics/                     Conference-year metric CSVs
    abstract_metrics/            Abstract metric CSVs

  database_load/               Neo4j data loading
    database_load.py             Upload scripts and query wrappers
    queries.yaml                 Cypher query definitions

  disambiguation/              Author name disambiguation
    disambiguate.py              Fuzzy name matching
    disambiguate_strict.py       Strict diacritic/abbreviation matching
    apply_disambiguation.py      Applies confirmed merges to CSV
    filter_unresolved.py         Separates resolved from unresolved pairs

  documentation/               Project documentation
    phase_1.md                   Data extraction and setup
    phase_2.md                   Results summary
    phase_3.md                   Limitations
    phase_4.md                   Reproducibility details
```

## Documentation

| Document | Contents |
|----------|----------|
| [Phase 1](documentation/phase_1.md) | Data extraction, cleaning, disambiguation, and upload |
| [Phase 2](documentation/phase_2.md) | Results summary with charts |
| [Phase 3](documentation/phase_3.md) | Limitations |
| [Phase 4](documentation/phase_4.md) | Detailed reproducibility instructions per script |
