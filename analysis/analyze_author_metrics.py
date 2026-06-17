import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np

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
    

def visualizeAuthorStatsForConference(conf=""):
    """
    Visualize author statistics across all years for a given conference.
    Creates line graphs with error bars showing standard deviation for average weighted betweenness, 
    unweighted betweenness, and degree.
    
    Args:
        conf (str): Conference abbreviation ('icse', 'icsa', 'ecsa')
    """
    years = list(range(2016, 2026))
    avg_unweighted_btw_list = []
    std_unweighted_btw_list = []
    avg_weighted_btw_list = []
    std_weighted_btw_list = []
    avg_degree_list = []
    std_degree_list = []
    
    # Collect statistics for all years
    for year in years:
        try:
            res = getTopAuthorStatsForConferenceAndYear(conf, year)
            avg_unweighted_btw, std_unweighted_btw, avg_weighted_btw, std_weighted_btw, top_unweighted_btw_authors, top_weighted_btw_authors, top_weighted_degree_authors = res
            
            avg_unweighted_btw_list.append(avg_unweighted_btw)
            std_unweighted_btw_list.append(std_unweighted_btw if not np.isnan(std_unweighted_btw) else 0)
            
            avg_weighted_btw_list.append(avg_weighted_btw)
            std_weighted_btw_list.append(std_weighted_btw if not np.isnan(std_weighted_btw) else 0)
            
            # Calculate average and std dev degree from the top degree authors
            if len(top_weighted_degree_authors) > 0:
                avg_degree = top_weighted_degree_authors['degree_weighted'].mean()
                std_degree = top_weighted_degree_authors['degree_weighted'].std()
            else:
                avg_degree = 0
                std_degree = 0
            avg_degree_list.append(avg_degree)
            std_degree_list.append(std_degree if not np.isnan(std_degree) else 0)
            
        except Exception as e:
            print(f"Error retrieving stats for {conf} {year}: {str(e)}")
            avg_unweighted_btw_list.append(np.nan)
            std_unweighted_btw_list.append(0)
            avg_weighted_btw_list.append(np.nan)
            std_weighted_btw_list.append(0)
            avg_degree_list.append(np.nan)
            std_degree_list.append(0)
    
    # Create visualization
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(f'{conf.upper()} Conference - Author Statistics Trends (2016-2025)', fontsize=16, fontweight='bold')
    
    # Plot 1: Average Unweighted Betweenness with error bars
    axes[0].errorbar(years, avg_unweighted_btw_list, yerr=std_unweighted_btw_list, 
                     marker='o', linestyle='-', linewidth=2, markersize=8, 
                     color='steelblue', ecolor='steelblue', capsize=5, capthick=2, alpha=0.7)
    axes[0].set_ylabel('Average Unweighted Betweenness', fontsize=12, fontweight='bold')
    axes[0].set_title('Average Unweighted Betweenness Centrality by Year')
    # axes[0].set_ylim(0.0, 0.002)
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_xticks(years)
    axes[0].set_xticklabels(years, rotation=45)
    
    # Plot 2: Average Weighted Betweenness with error bars
    axes[1].errorbar(years, avg_weighted_btw_list, yerr=std_weighted_btw_list, 
                     marker='s', linestyle='-', linewidth=2, markersize=8, 
                     color='coral', ecolor='coral', capsize=5, capthick=2, alpha=0.7)
    axes[1].set_ylabel('Average Weighted Betweenness', fontsize=12, fontweight='bold')
    axes[1].set_title('Average Weighted Betweenness Centrality by Year')
    # axes[1].set_ylim(0.0, 0.004)
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticks(years)
    axes[1].set_xticklabels(years, rotation=45)
    
    # Plot 3: Average Degree with error bars
    axes[2].errorbar(years, avg_degree_list, yerr=std_degree_list, 
                     marker='^', linestyle='-', linewidth=2, markersize=8, 
                     color='mediumseagreen', ecolor='mediumseagreen', capsize=5, capthick=2, alpha=0.7)
    axes[2].set_ylabel('Average Degree (Weighted)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Year', fontsize=12, fontweight='bold')
    axes[2].set_title('Average Degree (Weighted) by Year')
    axes[2].grid(axis='y', alpha=0.3)
    axes[2].set_xticks(years)
    axes[2].set_xticklabels(years, rotation=45)
    
    plt.tight_layout()
    
    # Save figure
    output_file = f'./analysis/{conf}_author_statistics_trend.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_file}")
    plt.close()
    
# Script to write findings across all three conferences, across the span of 10 years
# into an excel workbook, with a sheet per conference + year 
def loadExcelSheets():
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
    
if __name__ == "__main__":
    loadExcelSheets()