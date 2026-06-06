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


# number of authors to retrieve for each metric (top/bottom authors for a specific metric)
TOP_AUTHORS_RETRIEVAL_NUM = 50
BOTTOM_AUTHORS_RETRIEVAL_NUM = 10

def getTopAuthorStatsForConferenceAndYear(conf="", year=-1):
    # get authors data for specific year and conference
    authors = getAuthorsByConferenceAndYear(conf, year)
    renamed_df = df.rename(columns={"name": 'authors'})
    author_data = pd.merge(authors, renamed_df, on="authors", how="left")

    # Betweenness centrality metrics: avg, std
    avg_unweighted_btw = author_data['betweenness_unweighted'].mean()
    std_unweighted_btw = author_data['betweenness_unweighted'].std()
     
    avg_weighted_btw = author_data['betweenness_weighted'].mean()
    std_weighted_btw = author_data['betweenness_weighted'].std()
    
    # top authors per category
    top_unweighted_btw_authors = author_data.sort_values(by='betweenness_unweighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'betweenness_unweighted']]
    top_weighted_btw_authors = author_data.sort_values(by='betweenness_weighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'betweenness_weighted']]
    top_weighted_degree_authors = author_data.sort_values(by='degree_weighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'degree_weighted']]

    # do clustering coefficient once pulled
    # top_cluster_authors = author_data.sort_values(by='clustering_coefficient', ascending= False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'clustering_coefficient']]    
    
    return avg_unweighted_btw, std_unweighted_btw, avg_weighted_btw, std_weighted_btw, top_unweighted_btw_authors, top_weighted_btw_authors, top_weighted_degree_authors

    
# Script to write findings across all three conferences, across the span of 10 years
if __name__ == "__main__":
    conferences = ['icse', 'icsa', 'ecsa']
    years = range(2016, 2026)
    excel_file = './analysis/collaboration_network.xlsx'
    
    # set first_write to be true for creating the file
    # todo: set first_write to depend on xlsx file already existing
    first_write = True

    for conf in conferences:
        for year in years:
            try:
                res = getTopAuthorStatsForConferenceAndYear(conf, year)
                avg_unweighted_btw, std_unweighted_btw, avg_weighted_btw, std_weighted_btw, top_unweighted_btw_authors, top_weighted_btw_authors, top_weighted_degree_authors = res
                
                stats = {
                    'Avg Unweighted Betweenness': avg_unweighted_btw,
                    'Std Dev Unweighted Betweenness': std_unweighted_btw,
                    'Avg Weighted Betweenness': avg_weighted_btw,
                    'Std Dev Weighted Betweenness': std_weighted_btw,
                }
                
                dataframes = {
                    'Top Unweighted Betweenness': top_unweighted_btw_authors.reset_index(drop=True),
                    'Top Weighted Betweenness': top_weighted_btw_authors.reset_index(drop=True),
                    'Top Weighted Degree': top_weighted_degree_authors.reset_index(drop=True)
                }
                
                sheet_name = f'{conf.upper()}_{year}'
                # Use 'w' mode for first write, 'a' mode for subsequent writes
                write_mode = 'w' if first_write else 'a'
                with pd.ExcelWriter(excel_file, mode=write_mode, engine="openpyxl", if_sheet_exists="overlay" if write_mode == "a" else None) as writer:
                    stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
                    stats_df['Year'] = [year] * len(stats)
                    stats_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
                    
                    current_row = len(stats_df) + 3
                    for df_name, df_data in dataframes.items():
                        df_data.to_excel(writer, sheet_name=sheet_name, index=False, startrow=current_row)
                        current_row += len(df_data) + 3
                
                first_write = False
                print(f"  Wrote {sheet_name}")
                    
            except Exception as e:
                print(f"Error processing {conf} {year}: {str(e)}")
    
    print(f"\nCompleted - all results in {excel_file}")                
    
