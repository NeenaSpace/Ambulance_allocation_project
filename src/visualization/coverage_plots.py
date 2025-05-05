import matplotlib.pyplot as plt
import numpy as np
import os

def plot_coverage_analysis(coverage_by_zone_time, zones, t_periods, fairness_gap,
                          output_dir="./results/visualizations/consistency", 
                          filename="complete_coverage_analysis"):
    """
    Create comprehensive plots for coverage analysis
    
    Args:
        coverage_by_zone_time: Dictionary of coverage by zone and time
        zones: List of zones
        t_periods: Number of time periods
        fairness_gap: The optimal fairness gap value
        output_dir: Directory to save the plot
        filename: Filename to save the plot (without extension)
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 24))
    
    # Plot 1: Coverage over time for each zone
    for i in zones:
        coverage_values = [coverage_by_zone_time.get((i, t), 0) for t in range(t_periods)]
        ax1.plot(range(t_periods), coverage_values, 'o-', label=f'Zone {i}', linewidth=2, markersize=8)
    
    ax1.set_xlabel('Time Period', fontsize=12)
    ax1.set_ylabel('Coverage (1 = Covered, 0 = Not Covered)', fontsize=12)
    ax1.set_title('Zone Coverage Over Time', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Plot 2: Total coverage per zone
    total_coverage_per_zone = []
    zone_labels = []
    for i in zones:
        total = sum(coverage_by_zone_time.get((i, t), 0) for t in range(t_periods))
        total_coverage_per_zone.append(total)
        zone_labels.append(str(i))
    
    bars = ax2.bar(range(len(zones)), total_coverage_per_zone, color='skyblue')
    ax2.set_xlabel('Zones', fontsize=12)
    ax2.set_ylabel('Total Time Periods Covered', fontsize=12)
    ax2.set_title(f'Total Coverage per Zone (Fairness Gap: {fairness_gap})', fontsize=14)
    ax2.set_xticks(range(len(zones)))
    ax2.set_xticklabels(zone_labels, rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                 f'{int(height)}',
                 ha='center', va='bottom')
    
    # Plot 3: Coverage distribution histogram
    ax3.hist(total_coverage_per_zone, bins=t_periods, color='skyblue')
    ax3.set_xlabel('Number of Time Periods Covered', fontsize=12)
    ax3.set_ylabel('Number of Zones', fontsize=12)
    ax3.set_title('Distribution of Coverage Across Zones', fontsize=14)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure if output_dir is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f"{filename}.png"), bbox_inches='tight', dpi=300)
    
    return fig