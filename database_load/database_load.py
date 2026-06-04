from os import wait
import time
import random
import pandas as pd
import requests
import pyneoinstance

# Retrieving the Neo4j connection credentials from the config.yaml file
configs=pyneoinstance.load_yaml_file('./database_load/config.yaml')
queries = pyneoinstance.load_yaml_file('./database_load/queries.yaml')
creds=configs['credentials']

# Establishing the Neo4j connection
graph = pyneoinstance.Neo4jInstance(creds['uri'],creds['user'],creds['password'])

# Exponential backoff function - no external libraries
def backoff(operation_func, max_retries=5, base_delay=1.0):
    delay = base_delay
    
    for attempt in range(1, max_retries + 1):
        try:
            response =  operation_func()
            response.raise_for_status()
            return response 
        except Exception as e:
            if attempt == max_retries:
                raise e 
            print(f"Attempt {attempt} failed because of {e}, trying again with a {delay} delay")
            time.sleep(delay)
            delay *= 2
            
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

def addCoauthorsForPublication(pub_key):
    print("Adding coauthors for publication " + pub_key)
    authors = getAuthorsForPublication(pub_key)['a']
    # create coauthorship edges between all pairs of authors on this publication
    for i, author1 in enumerate(authors):
        for author2 in authors[i+1:]:
            author1_name = author1['author']
            author2_name = author2['author']
            graph.execute_write_query(
                query=queries['cypher']['add_coauthorship_edge'],
                database=creds['database'],
                parameters={
                    'author': author1_name,
                    'pub_key': pub_key,
                    'coauthor': author2_name
                })

def defineCoauthorshipEdges():
    publications = getAllPublications()['p']
    publications.apply(lambda p: addCoauthorsForPublication(p['pub_key']))
    
# get record by title 
def getPaperIdFromTitle(title):
    response = backoff(lambda: requests.get(f"https://api.semanticscholar.org/graph/v1/paper/search/match?query={title}"))
    if response.status_code == 400:
        return {"Error": "Bad query params"}
    elif response.status_code == 404:
        return {"Error": "Bad paper id"}
    data = response.json()
    if not data.get("data"):
        return {"Error": "Paper not found"}
    
    if response.status_code != 200 or 'message' in data:
        print(f"API Error: {data.get('message', 'Unknown API Error')}")
        return {"error": "API rate limit or error encountered"} 
    else:
        paper_id = data['data'][0]['paperId']
    return paper_id


# get citations from paper Id - selecting title for now
def getCitationFromId(id):
    response = backoff(lambda: requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{id}/citations"))
    if response.status_code == 400:
        return {"Error": "Bad query params" }
    elif response.status_code == 404:
        return {"Error": "Bad paper id"}
    else:
        data = response.json()
        return [paper['citingPaper'] for paper in data.get('data', [])]
    
def getCitationFromTitle(title):
    return getCitationFromId(getPaperIdFromTitle(title))
    
# get citation count from paper id 
def getCitationCountFromId(id):
    response = backoff(lambda: requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{id}?fields=citationCount"))
    if response.status_code == 400:
        return {"Error": "Bad query params" }
    elif response.status_code == 404:
        return {"Error": "Bad paper id"}
    else:
        data = response.json()
        try:
            return data["citationCount"]
        except (KeyError, IndexError, TypeError):
            return {"Error": "Something went wrong."}


def getCitationDetailCountByTitle(title):
    return getCitationCountFromId(getPaperIdFromTitle(title))


def getHIndexByAuthorName(author_name):
    response = backoff(lambda: requests.get(
        "https://api.semanticscholar.org/graph/v1/author/search",
        params={"query": author_name, "fields": "hIndex,citationCount,paperCount"}
    ))
    data = response.json()
    if not data.get('data') or len(data['data']) == 0:
        return {'h_index': None, 'citation_count': None, 'paper_count': None}
    # trying to find the best author -> return if non-disambiguated return the one with the most publications
    best_author = max(data['data'], key=lambda x: x.get('paperCount', 0))
    return {
        'h_index': best_author.get('hIndex'),
        'citation_count': best_author.get('citationCount'),
        'paper_count': best_author.get('paperCount')
    }
    
        
if __name__ == "__main__":
    # print(getCitationDetailCountByTitle("Deep Residual Learning for Image Recognition"))
     print(getHIndexByAuthorName("Jihyun Park"))