# Collaboration Network Analysis, Phase 1: Data and Setup

Jacob Chen, Adrian Rodriguez Vazquez, Madison Seal, Sahaj Baxi

## Data sets targeted

Our project targeted [DBLP](Link)'s records on three specific software engineering/architecture conferences: ICSE, ICSA, and ECSA. For each of these conferences, we gathered all publications posted between the years of 2015 and 2025, and found the authors for each.

## Data Extraction

Our initial data extraction was performed using the extract_dblp.py script, which generates the main author_publications.csv file, from which the rest of our data stems. Specifically, the script parses through publications containing the icsa/ecsa/icse keywords within their publication key. Each of the selected publications' authors are similarly extracted before being written to author_publications.csv. To run this script, your local device should download the DBLP XML dump as well as its corresponding DTD file for entity resolution, as DBLP uses custom XML classes and attributes.

## Description of cleaning activities

Our data was cleaned ad hoc as we created the author_publications.csv file; the only significant cleaning performed is a disambiguation script to account for similar author-publication records that are not easily distinguishable as two separate people. This is typically due to similar or misspelled names, unrecognized characters, etc. By performing disambiguation, we could identify all authors by name coupled with their disambiguation suffix, if needed.

### Disambiguation

_**/TODO/**_

### Data Upload

Data upload was achieved through a combination of Python scripts and leveraging existing data imports in the graph database services we selected. As our data upload is segmented, there are multiple discrete graph states which each upload step corresponds to.

#### Author-Publication Upload

Author-publication data upload was performed via Neo4j Aura's CSV upload integration, using the author_publications.csv file mentioned above. From this file, two node schemas -- authors (with author name as the primary key, possible only due to our disambiguation script), and publications (primary publication key, year, conference, and title as fields)-- and one relationship schema -- authorship, with no additional fields -- were created, respectively. The resulting graph connected author nodes to publication nodes via an 'AUTHORED' relationship.

#### Coauthorship Upload

The second graph state includes coauthorship edges between author nodes in addition to the existing author-publication authorship graph. This was implemented using a Python script, defineCoauthorshipEdges(), which requires a connection to the Neo4j instance as well as the author-publication graph uploaded in the format described above. For each publication in the graph, the script queries for its authors, then creates a new 'COAUTHORED_WITH' coauthorship edge (with the publication's pub-key as the edge's identifier field) for each unique author-author pair. As a result, authors will have both authorship edges to publications in the graph as well as coauthorship edges with every author they have shared a publication with.


## Data location

_**/TODO: dblp dump + DTD File/**_

## Dataset Access

Our dataset is accessible via the /csvs/ directory, which includes author_publications.csv as well as additional files such as ambiguous authors and statistical results.
