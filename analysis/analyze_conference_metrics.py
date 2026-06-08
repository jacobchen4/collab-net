import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np

# import database_load
sys.path.insert(0, './database_load')
from database_load import *


# for a conference, visualize avg number of publications/authors over the years
def getAllConferenceMetrics():
    authors_over_time = []
    pubs_over_time = []
    years = range(2016, 2026)

    for conf in ['icse', 'icsa', 'ecsa']:
        # reset the array
        authors_over_time = []
        pubs_over_time = []

        print(f"Visualizing {conf} data")
        for year in years:
            
            authors = getAuthorsByConferenceAndYear(conf=conf, year=year)
            pubs = getPublicationsByConferenceAndYear(conf=conf, year=year)
    
            authors_over_time.append(len(authors))
            pubs_over_time.append(len(pubs))
        
        # Create visualization
        fig, axes = plt.subplots(2, 1, figsize=(12, 14))
        fig.suptitle(f'{conf.upper()} Author/Publication Trends (2016-2025)', fontsize=16, fontweight='bold')
            
        axes[0].set_ylabel('Authors', fontsize=12, fontweight='bold')
        axes[0].set_title('Number of authors per year')
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].set_xticks(years)
        axes[0].set_xticklabels(years, rotation=45)

        axes[1].set_ylabel('Publications')
        axes[1].set_title('Number of publications per year')
        axes[1].grid(axis='y', alpha = 0.3)
        axes[1].set_xticks(years)
        axes[1].set_xticklabels(years, rotation=45)
        
        line_color = 'mediumseagreen' if conf == 'icsa' else 'coral' if conf == 'icse' else 'steelblue'
        axes[0].plot(years, authors_over_time, 
                     marker='^', linestyle='-', linewidth=2, markersize=8, 
                     color=line_color)

        axes[1].plot(years, pubs_over_time, marker='o', linestyle='-', linewidth=2, markersize=8, color=line_color)

        plt.tight_layout()
        
        # Save figure
        output_file = f'./analysis/images/{conf}_statistics_trend.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {output_file}")
        plt.close()

if __name__ == "__main__":
    getAllConferenceMetrics()
    