import time
import random
import pandas as pd
import pyneoinstance

# Retrieving the Neo4j connection credentials from the config.yaml file
configs=pyneoinstance.load_yaml_file('./database_load/config.yaml')
queries = pyneoinstance.load_yaml_file('./database_load/queries.yaml')
creds=configs['credentials']

# Establishing the Neo4j connection
graph = pyneoinstance.Neo4jInstance(creds['uri'],creds['user'],creds['password'])
    
def getPublicationsForAuthor(author):
    return graph.execute_read_query(
        queries['cypher']['get_publications_for_author'],
        parameters={'author': author})

def getAuthorsForPublication(pub_key):
    return graph.execute_read_query(
        queries['cypher']['get_authors_for_publication'],
        parameters={
            'pub_key': pub_key
        })

def getAllAuthors():
    return graph.execute_read_query(queries['cypher']['get_all_authors'])

def getAllPublications():
    return graph.execute_read_query(queries['cypher']['get_all_authors'])

def getCoauthorsForAuthor(author):
    publications = getPublicationsForAuthor(author)
    print(publications)
    
if __name__ == "__main__":
    # test
    print(getAllAuthors())
