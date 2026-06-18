# Collaboration Network Analysis, Phase 4: Reproducibility

Jacob Chen, Adrian Rodriguez Vazquez, Madison Seal, Sahaj Baxi

## Data Upload

See [phase_1.md](../../analysis\documentation\phase_1.md) for instructions on data extraction and upload.

## Data Analysis

Our data analysis was divided into three different parts: general conference metrics (trends), author metrics (trends + top X authors), and graph metrics (graph analysis). Each section has their corresponding Python scripts which synthesize data and visualize it in the form of charts, dataframes, or other.

### General Queries

Common methods or queries (e.g., get authors for publication and/or year, get coauthors of an author, etc.) can be found in [database_load.py](../../database_load\database_load.py) and [queries.yaml](../../database_load\queries.yaml). These queries form the basis of read and write queries used in our data upload and analysis scripts.

### Setup Scripts

Our analysis scripts require additional subgraphs or CSVs to properly execute. Before proceeding with the scripts mentioned in the sections below, ensure you have run the following:

1) fetch_graph.py

### Conference Metrics

Conference-specific metrics (such as publication/author count over time) can be generated using [analyze_conference_metrics.py](../../analysis\analyze_conference_metrics.py). After running this script, three images will be generated in the /images/ directory; each will show the change in author and publication count over time for a specific conference.

### Author Metrics

Author-specific metrics can be generated using [analyze_author_metrics.py](../../analysis\analyze_author_metrics.py). This script functions differently from the others, as it returns information related to a specific partition of the main graph. A total of 29 partitions are available (3 conferences x 10 years from 2016-2025, inclusive, excluding an ICSA 2017); running the method getTopAuthorStatsForConferenceAndYear() on a specific conference and year combination will yield the average and standard deviation degree centrality, betweenness centrality, weighted degree, and clustering coefficient for authors in that subgraph, as well as the top 10 authors for each metric, returning each as a dataframe.

Running the script will run the aforementioned method on all 33 partitions, compiling the data into three images (similarly located in images/) plotting each of the metrics over time. Additionally, loadExcelSheets() achieves the same functionality, creating an Excel spreadsheet (with each partition as a workbook) for ease of integration with other data.

### Graph Metrics

Graph metric computation relies on a local representation of the coauthorship network, built from the Neo4j graph using NetworkX. The pipeline begins with [fetch_graph.py](../../analysis/fetch_graph.py), which queries Neo4j for all author nodes and COAUTHORED_WITH edges, then constructs two graph representations: a MultiGraph (preserving one edge per shared publication) and a weighted Graph (where edge weights correspond to the number of shared publications between two authors, with a distance metric of 1/weight). Both graphs are serialized as pickle files in the /analysis/ directory for use by downstream scripts.

#### Metric Computation

Per-author network metrics are computed using [compute_metrics.py](../../analysis/compute_metrics.py), which loads the pickled graphs and calculates the following for each author: weighted degree (total co-authorship weight), total degree (all paper edges from the multigraph), weighted and unweighted betweenness centrality, weighted and unweighted clustering coefficient, and connected component membership. Weighted betweenness centrality uses the inverse-weight distance metric so that frequent collaborators are treated as closer in the network. The script supports an optional `--approx K` flag for approximate betweenness computation using K sample nodes, which is useful for larger graphs. Results are written to analysis/author_metrics.csv.

#### Subgraph Generation

To enable temporal and conference-specific analysis, [generate_subgraphs.py](../../analysis/generate_subgraphs.py) partitions the full network into 33 subgraphs (3 conferences x 11 years). For each conference-year combination, the script queries Neo4j for the corresponding filtered subgraph, builds both graph representations, and computes the same set of per-author metrics. The resulting graphs and metric CSVs are saved to analysis/graphs/ and analysis/metrics/, respectively.

#### Community Detection

Research communities within the coauthorship network are identified using [detect_communities.py](../../analysis/detect_communities.py), which applies the Louvain algorithm (seeded for reproducibility) to the full weighted graph. The script outputs analysis/author_communities.csv, listing each author's community assignment and community size, sorted by descending community size.

#### Structural Role Classification

Authors are classified into structural roles based on their network position using [classify_roles.py](../../analysis/classify_roles.py). Using percentile thresholds (25th and 75th) on degree, betweenness, and clustering, each author is assigned one of five roles: broker (high betweenness, low clustering), hub (high degree, low clustering), embedded (high clustering, low betweenness), peripheral (low degree), or core (well-connected without extremes in any single dimension). Role assignments are written to analysis/author_roles.csv.

#### Bridge Author Identification

Authors who published across multiple conferences are identified using [bridge_authors.py](../../analysis/bridge_authors.py). The script groups publications by conference, flags authors appearing in two or more of ICSA, ICSE, and ECSA, and merges the results with full network metrics. The output, analysis/bridge_authors.csv, includes each bridge author's conference memberships alongside their centrality measures.

#### Abstract Structural Metrics

Higher-level structural properties of the coauthorship network are computed using [compute_abstract_metrics.py](../../analysis/compute_abstract_metrics.py). This script is organized into eight independent tasks (numbered 5–12), each of which can be run selectively via the `--tasks` flag. Results are written to analysis/abstract_metrics/ (CSVs) and analysis/plots/ (PNGs). The tasks are as follows:

- **Power-law test (Task 5):** Tests whether the degree distribution follows a power law (indicative of a scale-free network) using maximum likelihood estimation and a log-likelihood ratio comparison against a log-normal alternative. Produces a CCDF plot on log-log axes.
- **Small-world coefficient (Task 6):** Computes the Watts-Strogatz sigma and omega coefficients on the giant connected component, comparing the network's clustering and average path length against Erdos-Renyi random graph baselines.
- **Degree assortativity (Task 7):** Measures Newman's degree assortativity coefficient r for the full graph and across all conference-year subgraphs, producing a time-series plot per conference. Positive r indicates hub-to-hub clustering; negative r indicates hubs connecting to peripheral authors.
- **Temporal role transitions (Task 8):** Classifies authors into structural roles for each conference-year snapshot using per-snapshot percentile thresholds, then tracks role transitions for authors appearing in consecutive years at the same conference. Outputs include a 5x5 transition probability matrix with heatmap and role proportion trends over time.
- **Community persistence (Task 9):** Measures year-over-year stability of research communities by running Louvain community detection on consecutive yearly subgraphs and computing best-match Jaccard similarity scores between communities across years.
- **Conference cross-pollination (Task 10):** For each year, measures the fraction of ICSA and ECSA authors who also published at ICSE, tracking whether the software-architecture and broader SE communities are converging or diverging over time.
- **K-shell decomposition (Task 11):** Assigns each author a k-core number (the highest k for which they belong to the k-core subgraph), providing a parameter-free measure of structural embeddedness. Produces a k-shell histogram and boxplots grouped by structural role.
- **Author retention (Task 12):** Tracks when each author first and last appears at each conference and constructs mean retention (survival) curves per conference across debut cohorts, measuring how long authors remain active after their first publication.

We deemed a subset of tasks to give meaningful results, notably tasks 5, 6, and 11.

#### Visualization

High-level summaries and plots for the above analyses are generated using [compute_trivial_metrics.py](../../analysis/compute_trivial_metrics.py). This script produces degree histograms, structural role distributions with boxplots, community size distributions, and cross-conference bridge author breakdowns, all saved to the /plots/ directory.

### Statistical Tests

Statistical analysis performed on graph partitions was achieved through the script in [analyze_statistical_significance.py](../../analysis/analyze_statistical_significance.py). Please note that running this script requires the /metrics/ folder to be populated with the partition CSV files, achieved by running [compute_metrics.py](../compute_metrics.py). Running analyze_statistical_significance.py results in a new CSV file titled 'statistical_test_results.csv', where each row is a test performed on a specific aggregate coupled with its result, p-value, effect size, and verdict of significance.
