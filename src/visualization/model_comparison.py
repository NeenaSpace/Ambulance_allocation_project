import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

def plot_model_comparison(df, output_dir="./results/visualizations/comparison", filename="model_comparison"):
    """
    Plot comparison between different model formulations
    
    Args:
        df: DataFrame with model comparison data
        output_dir: Directory to save the plot
        filename: Filename to save the plot (without extension)
    """
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 1: Variables comparison
    orig_sizes = df['config_size'].unique()
    orig_vars = df.groupby('config_size')['orig_vars'].first()
    axes[0,0].plot(orig_sizes, orig_vars, 'o-', label='Original', linewidth=2, markersize=8)
    
    freq_bounds = sorted(df['freq_bound'].unique())
    for freq in freq_bounds:
        subset = df[df['freq_bound'] == freq]
        axes[0,0].plot(subset['config_size'], subset['bin_vars'], 's-', 
                       label=f'Binary (Max={freq})', linewidth=2, markersize=8)
    axes[0,0].set_xlabel('Number of Configurations', fontsize=12)
    axes[0,0].set_ylabel('Number of Variables', fontsize=12)
    axes[0,0].set_title('Model Size: Variables Comparison', fontsize=14)
    axes[0,0].legend(fontsize=10)
    axes[0,0].grid(True, alpha=0.3)
    
    # Plot 2: Constraints comparison
    orig_constrs = df.groupby('config_size')['orig_constrs'].first()
    axes[0,1].plot(orig_sizes, orig_constrs, 'o-', label='Original', linewidth=2, markersize=8)
    
    for freq in freq_bounds:
        subset = df[df['freq_bound'] == freq]
        axes[0,1].plot(subset['config_size'], subset['bin_constrs'], 's-', 
                       label=f'Binary (Max={freq})', linewidth=2, markersize=8)
    axes[0,1].set_xlabel('Number of Configurations', fontsize=12)
    axes[0,1].set_ylabel('Number of Constraints', fontsize=12)
    axes[0,1].set_title('Model Size: Constraints Comparison', fontsize=14)
    axes[0,1].legend(fontsize=10)
    axes[0,1].grid(True, alpha=0.3)
    
    # Plot 3: Solve time comparison
    orig_time = df.groupby('config_size')['orig_time'].first()
    axes[1,0].plot(orig_sizes, orig_time, 'o-', label='Original', linewidth=2, markersize=8)
    
    for freq in freq_bounds:
        subset = df[df['freq_bound'] == freq]
        axes[1,0].plot(subset['config_size'], subset['bin_time'], 's-', 
                       label=f'Binary (Max={freq})', linewidth=2, markersize=8)
    axes[1,0].set_xlabel('Number of Configurations', fontsize=12)
    axes[1,0].set_ylabel('Solve Time (seconds)', fontsize=12)
    axes[1,0].set_title('Computational Performance Comparison', fontsize=14)
    axes[1,0].legend(fontsize=10)
    axes[1,0].grid(True, alpha=0.3)
    
    # Plot 4: Objective value comparison
    orig_obj = df.groupby('config_size')['orig_obj'].first()
    axes[1,1].plot(orig_sizes, orig_obj, 'o-', label='Original', linewidth=2, markersize=8)
    
    for freq in freq_bounds:
        subset = df[df['freq_bound'] == freq]
        axes[1,1].plot(subset['config_size'], subset['bin_obj'], 's-', 
                       label=f'Binary (Max={freq})', linewidth=2, markersize=8)
    axes[1,1].set_xlabel('Number of Configurations', fontsize=12)
    axes[1,1].set_ylabel('Objective Value (Fairness Gap)', fontsize=12)
    axes[1,1].set_title('Solution Quality Comparison', fontsize=14)
    axes[1,1].legend(fontsize=10)
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure if output_dir is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f"{filename}.png"), bbox_inches='tight', dpi=300)
    
    return fig