import time
import random
import os
import pandas as pd
import pyneoinstance
import datetime

# Retrieving the Neo4j connection credentials from the config.yaml file
configs=pyneoinstance.load_yaml_file('config.yaml')
queries = pyneoinstance.load_yaml_file('./database_load/queries.yaml')
creds=configs['credentials']

# Establishing the Neo4j connection
graph = pyneoinstance.Neo4jInstance(creds['uri'],creds['user'],creds['password'])
    
def getPublicationsForAuthor(author):
    return graph.execute_read_query(
        query=queries['cypher']['get_publications_for_author'],
        database=creds['database'],
        parameters={'author': author})

def getAuthorsForPublication(pub_key):
    return graph.execute_read_query(
        query=queries['cypher']['get_authors_for_publication'],
        database=creds['database'],
        parameters={
            'pub_key': pub_key
        })

def getAllAuthors():
    return graph.execute_read_query(queries['cypher']['get_all_authors'])

def getAllPublications():
    return graph.execute_read_query(queries['cypher']['get_all_publications'])

def getAuthorsByYear(year):
    return graph.execute_read_query(queries['cypher']['get_authors_by_year'], parameters={'year': year})

def getPublicationsByYear(year):
    return graph.execute_read_query(queries['cypher']['get_publications_by_year'], parameters={'year': year})

def getAuthorsByConference(conf):
    return graph.execute_read_query(queries['cypher']['get_authors_by_conference'], parameters={"conf": conf})

def getPublicationsByConference(conf):
    return graph.execute_read_query(queries['cypher']['get_publications_by_conference'], parameters={"conf": conf})

def getAuthorsByConferenceAndYear(conf, year):
    return graph.execute_read_query(queries['cypher']['get_authors_by_conference_and_year'], parameters={'year': year, 'conf': conf})

def getPublicationsByConferenceAndYear(conf, year):
    return graph.execute_read_query(queries['cypher']['get_publications_by_conference_and_year'], parameters={'year': year, 'conf': conf}) 

# Returns a series of objects ({pub_key, coauthors}) that represents the given author's
# coauthors and their corresponding publications
def getCoauthorsForAuthor(author):
    publications = getPublicationsForAuthor(author)['p']
    
    # helper method to get unique coauthors given a publication
    def getCoauthoredPublications(publication) :
        coauthors = set()
        authors = getAuthorsForPublication(publication['pub_key'])
        # filter authors to remove selected author
        filtered_authors = authors[authors['a'].apply(lambda x: x['author']) != author]
        # add each co-author to coauthors set
        for _, row in filtered_authors.iterrows():
            coauthors.add(row['a']['author'])
        return coauthors
    
    return publications.apply(lambda p: {
        'pub_key': p['pub_key'],
        'coauthors': getCoauthoredPublications(p)
        })

def getAllPublicationsWithAuthors():
    query = """
    MATCH (p:publication)-[:AUTHORED]-(a:author)
    RETURN p.pub_key as pub_key, COLLECT(a.author) as authors
    """
    return graph.execute_read_query(query)

def addCoauthorsForAuthor(author):
    # get publication-coauthor objects for given author
    pubCoauthorsObjs = getCoauthorsForAuthor(author)
    print("Found coauthors/publications for " + author)
    for coauthorsObj in pubCoauthorsObjs:
        pub_key = coauthorsObj['pub_key']
        print("Adding coauthors for publication " + pub_key)
        # for each coauthor in each publication, add the corresponding coauthorship edge
        for coauthor in coauthorsObj['coauthors']:
            graph.execute_write_query(
                query=queries['cypher']['add_coauthorship_edge'],
                database=creds['database'],
                parameters={
                    'author': author,
                    'pub_key': pub_key,
                    'coauthor': coauthor
                })

def addCoauthorsForPublication(pub_key, authors):
    # if one author, no edges created
    if len(authors) < 2:
        return {'success': True, 'edges_created': 0}
    
    # Create author-coauthor pairs
    author_pairs = []
    for i, author1 in enumerate(authors):
        for author2 in authors[i+1:]:
            author_pairs.append({'author': author1['author'], 'coauthor': author2['author']})
    
    try:
        result = graph.execute_write_query(
            query=queries['cypher']['add_coauthorship_edges_batch'],
            database=creds['database'],
            parameters={
                'pub_key': pub_key,
                'author_pairs': author_pairs
            })
        
        if not result:
            return {'success': True, 'edges_created': 0}
        else:
            return {'success': True, 'edges_created': result['relationships_created']}
    except Exception as e:
        return {'success': False, 'error': f"Batch query failed for {pub_key} with {len(author_pairs)} pairs: {str(e)}"}

def defineCoauthorshipEdges(publications):
    failed_publications = []
    total_edges = 0
    
    for idx, pub in publications.items():
        pub_key = pub['pub_key']
        if idx % 100 == 0:
            print(f"100 publication-coauthors added, currently on {pub_key}")
        # Get authors for this publication
        try:
            authors = getAuthorsForPublication(pub_key)['a']            
            # Add coauthorship edges using batch query
            result = addCoauthorsForPublication(pub_key, authors)
            
            if result['success']:
                total_edges += result['edges_created']
            elif not result:
                print(f"Added no edges for publication {pub_key}")
            else:
                print(f"Error at publication {pub_key}: {result['error']}")
                failed_publications.append({'pub_key': pub_key, 'error': result['error']})
        except Exception as e:
            print(f"Error processing publication {pub_key}: {str(e)}")
            failed_publications.append({'pub_key': pub_key, 'error': str(e)})
    
    # Log results and failures
    print(f"Total coauthorship edges created: {total_edges}")
    
    if failed_publications:
        print(f"\nFailed publications: {len(failed_publications)}")
        # Retry failed publications
        if len(failed_publications) > 0:
            print(f"Retrying failed publications")
            time.sleep(60)
            failed_pubs_df = pd.DataFrame(failed_publications)
            
            failed_pubs_series = pd.Series([{'pub_key': row['pub_key']} for _, row in failed_pubs_df.iterrows()])
            defineCoauthorshipEdges(failed_pubs_series)

# Use this method first to define the authorship graph, followed by defineCoauthorshipEdges
# (which assumes nodes already exist)
def defineAuthorshipNodesAndEdges(batch_size=100):
    df = pd.read_csv('csvs/author_publications.csv')
    failed_batches = []
    total_edges = 0
    batch = []

    # Execute a single batched merge for the accumulated rows
    def flush(rows):
        nonlocal total_edges
        result = graph.execute_write_query(
            query=queries['cypher']['merge_authorship_nodes_and_edges_batch'],
            database=creds['database'],
            parameters={'rows': rows})
        total_edges += result['edges_created'] if result is not None else 0

    for idx, row in df.iterrows():
        batch.append({
            'author': row['author'],
            'pub_key': row['pub_key'],
            'title': None if pd.isna(row['title']) else row['title'],
            'year': int(row['year']),
            'conference': row['conference'],
        })
        # When the batch is full, merge it and reset
        if len(batch) >= batch_size:
            try:
                flush(batch)
                print(f"Processed {idx + 1} rows, last pub_key {row['pub_key']}")
            except Exception as e:
                print(f"Error merging batch ending at row {idx + 1}: {str(e)}")
                failed_batches.append({'rows': list(batch), 'error': str(e)})
            batch = []

    # Flush the final partial batch
    if batch:
        try:
            flush(batch)
        except Exception as e:
            print(f"Error merging final batch: {str(e)}")
            failed_batches.append({'rows': list(batch), 'error': str(e)})

    print(f"Total AUTHORED edges merged: {total_edges}")

    # Retry any failed batches once after a delay
    if failed_batches:
        print(f"\nFailed batches: {len(failed_batches)}")
        print(f"Retrying failed batches")
        time.sleep(60)
        still_failed = []
        for failed in failed_batches:
            try:
                flush(failed['rows'])
            except Exception as e:
                print(f"Retry failed: {str(e)}")
                still_failed.append({'rows': failed['rows'], 'error': str(e)})
        if still_failed:
            print(f"Batches still failing after retry: {len(still_failed)}")

# Helper method to find the leftoff point
# last_publication serves as a checkpoint for whatever publication our coauthorship 
# script left off at, in the case of network interruptions or the like.
def findLeftoff(pub_key):
    publications = getAllPublications()
    # index of error - 2 for failsafe
    last_index = publications['p'].index[publications['p'].apply(lambda p: p['pub_key']) == pub_key][0] - 2
    return publications['p'][last_index:].apply(lambda x: x['pub_key'])


# Retrieves subgraph instances (e.g, filtering by year, conference)
def getSubgraph(year = -1, conf  = ""):
    # if conference provided
    if conf:
        # if both conf and year
        if year != -1:
            return graph.execute_read_query(queries['cypher']['get_graph_for_conference_and_year'], parameters={'year': year, 'conf': conf.lower()})
        # if only conference
        else:
            return graph.execute_read_query(queries['cypher']['get_graph_for_conference'], parameters={'conf': conf.lower()})
    # if no conference and no year
    elif year == -1:
        return None
    else:
        return graph.execute_read_query(queries['cypher']['get_graph_for_year'], parameters={'year': year})
