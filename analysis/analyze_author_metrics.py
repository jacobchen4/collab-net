import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np

# import database_load
sys.path.insert(0, './database_load')
from database_load import *

# number of authors to retrieve for each metric (top/bottom authors for a specific metric)
TOP_AUTHORS_RETRIEVAL_NUM = 10

def getTopAuthorStatsForConferenceAndYear(conf="", year=-1):
    if conf == "" or year == -1:
        print("Conference or year not provided.")
        return None
    
    author_data = pd.read_csv(f'./analysis/metrics/{conf.lower()}_{year}_author_metrics.csv').rename(columns={'name': 'authors'})
    
    # Betweenness centrality metrics: avg, std
    avg_unweighted_btw = author_data['betweenness_unweighted'].mean()
    std_unweighted_btw = author_data['betweenness_unweighted'].std()
     
    avg_weighted_btw = author_data['betweenness_weighted'].mean()
    std_weighted_btw = author_data['betweenness_weighted'].std()

    avg_cluster_weighted = author_data['clustering_weighted'].mean()
    std_cluster_weighted = author_data['clustering_weighted'].std()

    avg_cluster_weighted = author_data['clustering_weighted'].mean()
    std_cluster_weighted = author_data['clustering_weighted'].std()
    
    avg_degree_weighted = author_data['degree_weighted'].mean()
    std_degree_weighted = author_data['degree_weighted'].std()
    
    # top authors per category
    top_unweighted_btw_authors = author_data.sort_values(by='betweenness_unweighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'betweenness_unweighted']]
    top_weighted_btw_authors = author_data.sort_values(by='betweenness_weighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'betweenness_weighted']]
    top_weighted_degree_authors = author_data.sort_values(by='degree_weighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'degree_weighted']]
    top_weighted_cluster_authors = author_data.sort_values(by='clustering_weighted', ascending=False).head(TOP_AUTHORS_RETRIEVAL_NUM)[['authors', 'clustering_weighted']]
    
    return avg_unweighted_btw, std_unweighted_btw, avg_weighted_btw, std_weighted_btw, avg_cluster_weighted, std_cluster_weighted, avg_degree_weighted, std_degree_weighted, top_unweighted_btw_authors, top_weighted_btw_authors, top_weighted_degree_authors, top_weighted_cluster_authors


def visualizeAuthorStatsForConference(conf=""):
    """
    Visualize author statistics across all years for a given conference.
    Creates line graphs with error bars showing standard deviation for average weighted betweenness, 
    unweighted betweenness, degree, and weighted clustering coefficient.
    unweighted betweenness, degree, and weighted clustering coefficient.
    
    Args:
        conf (str): Conference abbreviation ('icse', 'icsa', 'ecsa')
    """
    years = list(range(2015, 2026))
    avg_unweighted_btw_list = []
    std_unweighted_btw_list = []
    avg_weighted_btw_list = []
    std_weighted_btw_list = []
    avg_degree_list = []
    std_degree_list = []
    avg_cluster_list = []
    std_cluster_list = []
   
    
    # Collect statistics for all years
    for year in years:
        try:
            res = getTopAuthorStatsForConferenceAndYear(conf, year)
            avg_unweighted_btw, std_unweighted_btw, avg_weighted_btw, std_weighted_btw, avg_cluster_weighted, std_cluster_weighted, avg_degree_weighted, std_degree_weighted, top_unweighted_btw_authors, top_weighted_btw_authors, top_weighted_degree_authors, top_weighted_cluster_authors = res
            
            avg_unweighted_btw_list.append(avg_unweighted_btw)
            std_unweighted_btw_list.append(std_unweighted_btw if not np.isnan(std_unweighted_btw) else 0)
            
            avg_weighted_btw_list.append(avg_weighted_btw)
            std_weighted_btw_list.append(std_weighted_btw if not np.isnan(std_weighted_btw) else 0)
            
            avg_degree_list.append(avg_degree_weighted)
            std_degree_list.append(std_degree_weighted if not np.isnan(std_degree_weighted) else 0)
            
            # Clustering coefficient
            avg_cluster_list.append(avg_cluster_weighted)
            std_cluster_list.append(std_cluster_weighted if not np.isnan(std_cluster_weighted) else 0)
            
        except Exception as e:
            print(f"Error retrieving stats for {conf} {year}: {str(e)}")
            avg_unweighted_btw_list.append(np.nan)
            std_unweighted_btw_list.append(0)
            avg_weighted_btw_list.append(np.nan)
            std_weighted_btw_list.append(0)
            avg_degree_list.append(np.nan)
            std_degree_list.append(0)
            avg_cluster_list.append(np.nan)
            std_cluster_list.append(0)
    
    # Create visualization
    fig, axes = plt.subplots(4, 1, figsize=(12, 14))
    fig.suptitle(f'{conf.upper()} Conference - Author Statistics Trends (2015-2025)', fontsize=16, fontweight='bold')
    
    # Plot 1: Average Unweighted Betweenness with error bars
    axes[0].errorbar(years, avg_unweighted_btw_list, yerr=std_unweighted_btw_list, 
                     marker='o', linestyle='-', linewidth=2, markersize=8, 
                     color='steelblue', ecolor='steelblue', capsize=5, capthick=2, alpha=0.7)
    axes[0].set_ylabel('Average Unweighted Betweenness', fontsize=12, fontweight='bold')
    axes[0].set_title('Average Unweighted Betweenness Centrality by Year')
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_xticks(years)
    axes[0].set_xticklabels(years, rotation=45)
    
    # Plot 2: Average Weighted Betweenness with error bars
    axes[1].errorbar(years, avg_weighted_btw_list, yerr=std_weighted_btw_list, 
                     marker='s', linestyle='-', linewidth=2, markersize=8, 
                     color='coral', ecolor='coral', capsize=5, capthick=2, alpha=0.7)
    axes[1].set_ylabel('Average Weighted Betweenness', fontsize=12, fontweight='bold')
    axes[1].set_title('Average Weighted Betweenness Centrality by Year')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticks(years)
    axes[1].set_xticklabels(years, rotation=45)
    
    # Plot 3: Average Degree with error bars
    axes[2].errorbar(years, avg_degree_list, yerr=std_degree_list, 
                     marker='^', linestyle='-', linewidth=2, markersize=8, 
                     color='mediumseagreen', ecolor='mediumseagreen', capsize=5, capthick=2, alpha=0.7)
    axes[2].set_ylabel('Average Degree (Weighted)', fontsize=12, fontweight='bold')
    axes[2].set_title('Average Degree (Weighted) by Year')
    axes[2].grid(axis='y', alpha=0.3)
    axes[2].set_xticks(years)
    axes[2].set_xticklabels(years, rotation=45)
    
    # Plot 4: Average Clustering Coefficient with error bars
    axes[3].errorbar(years, avg_cluster_list, yerr=std_cluster_list, 
                     marker='D', linestyle='-', linewidth=2, markersize=8, 
                     color='mediumpurple', ecolor='mediumpurple', capsize=5, capthick=2, alpha=0.7)
    axes[3].set_ylabel('Average Clustering Coefficient', fontsize=12, fontweight='bold')
    axes[3].set_xlabel('Year', fontsize=12, fontweight='bold')
    axes[3].set_title('Average Weighted Clustering Coefficient by Year')
    axes[3].grid(axis='y', alpha=0.3)
    axes[3].set_xticks(years)
    axes[3].set_xticklabels(years, rotation=45)
    
    plt.tight_layout()
    
    # Save figure
    output_file = f'./analysis/images/{conf}_author_statistics_trend.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_file}")
    plt.close()
    
# Script to write findings across all three conferences, across the span of 10 years
# into an excel workbook, with a sheet per conference + year 
def loadExcelSheets():
    conferences = ['icse', 'icsa', 'ecsa']
    years = range(2015, 2026)
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
    for conf in ['icse', 'icsa', 'ecsa']:
        visualizeAuthorStatsForConference(conf)