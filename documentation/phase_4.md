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

Author-specific metrics can be generated using [analyze_author_metrics.py](../../analysis\analyze_author_metrics.py). This script functions differently from the others, as it returns information related to a specific partition of the main graph. A total of 33 partitions are available (3 conferences x 11 years from 2015-2025, inclusive); running the method getTopAuthorStatsForConferenceAndYear() on a specific conference and year combination will yield the average and standard deviation degree centrality, betweenness centrality, weighted degree, and clustering coefficient for authors in that subgraph, as well as the top 10 authors for each metric, returning each as a dataframe.

Running the script will run the aforementioned method on all 33 partitions, compiling the data into three images (similarly located in images/) plotting each of the metrics over time. Additionally, loadExcelSheets() achieves the same functionality, creating an Excel spreadsheet (with each partition as a workbook) for ease of integration with other data.

### Graph Metrics

_*TODO*_

### Statistical Tests

Statistical analysis performed on graph partitions was achieved through the script in [analyze_statistical_significance.py](../../analysis/analyze_statistical_significance.py). Please note that running this script requires the /metrics/ folder to be populated with the partition CSV files, achieved by running [compute_metrics.py](../compute_metrics.py). Running analyze_statistical_significance.py results in a new CSV file titled 'statistical_test_results.csv', where each row is a test performed on a specific aggregate coupled with its result, p-value, effect size, and verdict of significance.
