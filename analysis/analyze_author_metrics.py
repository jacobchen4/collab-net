import pandas as pd
import sys

# import database_load
sys.path.insert(0, './database_load')
from database_load import *

df = pd.read_csv('./analysis/author_metrics.csv')

# By conference
# General graph observations
# Clustering, etc.
# Take ~100 (?) authors with the highest/lowest of each metric, note their position in the graph + who they coauthor with
# For top/bottom 20 (?), corroborate with semantic scholar api to get details about their h-index?, citations, etc.

# By Year
# general shape and distribution of graph
# Average betweenness, degree, etc. for authors publishing in this year + conference

def getAuthorStatisticsPerConfAndYear(conf: String, year: Int):
    
    # get authors data for specific year and conference
    authors = getAuthorsByConferenceAndYear(conf, year)
    renamed_df = df.rename(columns={"name": 'authors'})
    author_data = pd.merge(authors, renamed_df, on="authors", how="left")

    # Betweenness centrality metrics: avg, std
    avg_unweighted_btw = author_data['betweenness_unweighted'].mean()
    std_unweighted_btw = author_data['betweenness_unweighted'].std()
     
    avg_weighted_btw = author_data['betweenness_weighted'].mean()
    std_weighted_btw = author_data['betweenness_weighted'].std()

    print(avg_unweighted_btw, avg_weighted_btw, std_unweighted_btw, std_weighted_btw)

if __name__ == "__main__":
    getAuthorStatisticsPerConfAndYear('icse', 2020)