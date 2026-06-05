import time
import random
import os
import pandas as pd
import pyneoinstance
import datetime
from database_load import *

# Retrieving the Neo4j connection credentials from the config.yaml file
configs=pyneoinstance.load_yaml_file('./database_load/config.yaml')
queries = pyneoinstance.load_yaml_file('./database_load/queries.yaml')
creds=configs['credentials']

# Establishing the Neo4j connection
graph = pyneoinstance.Neo4jInstance(creds['uri'],creds['user'],creds['password'])


# Returns a dataframe containing [author, num_publications] ordered by num_publications
def getAuthorPublicationDegreeCentrality():
    df = graph.execute_read_query(
        queries['cypher']['get_author-publication_degree_centrality'],
        database=creds['database']
        )
    return df   

def getGraphStateByYear(year: int):
    df = graph.execute_read_query(
        queries['cypher']['get_graph_state_by_year'],
        database=creds['database'],
        parameters={
            'year': year
        }
    )
    return df


# Retrieves the coauthor network for a specific author
# @param num_layers : the number of layers to traverse through 
# (equivalent to degree of separation e.g, 3 layers = coauthors of coauthors of coauthors)
def getCoauthorNetwork(author, num_layers=3, coauthors_set=set([]), visited_coauthors=set([])):    
    # if at 0 layers, return
    if num_layers < 1:
        return coauthors_set
    
    # add current coauthor to visited_coauthors
    visited_coauthors.add(author)
    
    # for each coauthor object -> extract coauthors set -> add each coauthor to coauthors set
    coauthors= getCoauthorsForAuthor(author).apply(
        lambda obj: obj['coauthors']
        ).apply(
            lambda set: coauthors_set.update(set)
        )
                
    return coauthors_set.apply(lambda author: getCoauthorNetwork(author))

# Finds all islands on a graph.
def findGraphIslands():
    

if __name__ == "__main__":
    print(getCoauthorNetwork("Ian Gorton", num_layers=10))