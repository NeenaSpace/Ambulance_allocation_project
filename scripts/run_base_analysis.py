#!/usr/bin/env python3
"""
Script to run analysis on all bases together
"""

import os
import sys
import argparse
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing.data_loader import DataLoader
from src.models.base_model import BaseModel

def main():
    parser = argparse.ArgumentParser(description='Run analysis for all bases together with different configuration sizes')
    parser.add_argument('--instance', type=str, required=True, help='Instance name (e.g., 50-3004-6-7-35)')
    parser.add_argument('--periods', type=int, default=6, help='Number of time periods')
    parser.add_argument('--ambulances', type=int, default=50, help='Number of ambulances')
    parser.add_argument('--size', type=int, default=50, help='Graph size (nodes)')
    parser.add_argument('--min-configs', type=int, default=100, help='Minimum number of configurations')
    parser.add_argument('--max-configs', type=int, default=None, help='Maximum number of configurations')
    parser.add_argument('--num-steps', type=int, default=8, help='Number of configuration sizes to test')
    parser.add_argument('--time-limit', type=int, default=600, help='Time limit for each optimization (seconds)')
    parser.add_argument('--data-dir', type=str, default='./data/raw', help='Directory containing raw data')
    parser.add_argument('--config-dir', type=str, default='./data/processed', help='Directory containing configurations')
    parser.add_argument('--results-dir', type=str, default='./results', help='Directory to save results')
    
    args = parser.parse_args()
    
    # Create results directories
    model_output_dir = os.path.join(args.results_dir, "model_outputs", "all_bases")
    vis_output_dir = os.path.join(args.results_dir, "visualizations", "analysis")
    os.makedirs(model_output_dir, exist_ok=True)
    os.makedirs(vis_output_dir, exist_ok=True)
    
    # Load data
    loader = DataLoader(args.data_dir)
    G = loader.load_graph(args.instance, args.size)
    all_base_nodes = loader.load_all_bases(args.instance, args.size)
    
    # Create adjacency dictionary
    adjacency = {node: set(G.neighbors(node)) for node in G.nodes}
    zones = list(G.nodes)
    
    # Load configurations
    config_path = os.path.join(args.config_dir, str(args.size), 
                              f"{args.instance}-all_bases_t0_{args.periods-1}", 
                              "configs.csv")
    df_full = pd.read_csv(config_path)
    total_configs = len(df_full)
    
    # Determine max_configs if not provided
    if args.max_configs is None:
        args.max_configs = total_configs
    
    # Create log-spaced config sizes
    config_sizes = np.logspace(np.log10(args.min_configs), 
                             np.log10(args.max_configs), 
                             args.num_steps, dtype=int).tolist()
    config_sizes = sorted(list(set(config_sizes)))  # Remove duplicates and sort
    
    print(f"Running analysis for all bases with config sizes: {config_sizes}")
    
    # Initialize model
    license_path = "./data/raw/gurobi.lic"
    params = {}
    with open(license_path, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=')
                if key == 'LICENSEID':
                    params[key] = int(value)  # Convert LICENSEID to int
                else:
                    params[key] = value
    
    model = BaseModel(params, model_output_dir)
    model.initialize_environment()
    
    # Run for each config size
    results = []
    
    for num_configs in config_sizes:
        print(f"\nSolving for {num_configs} configurations...")
        
        # Prepare configurations and coverage matrix
        df = df_full.head(num_configs)
        configs = []
        for _, row in df.iterrows():
            cfg = []
            for t in range(args.periods):
                cfg.append((row[f"t{t}_x"], row[f"t{t}_y"]))
            configs.append(cfg)
        
        # Build coverage matrix
        b = {}
        for c_idx, config in enumerate(configs):
            for t, zone in enumerate(config):
                coverage = {zone} | adjacency.get(zone, set())
                for z in coverage:
                    b[z, t, c_idx] = 1
        
        # Build and solve model
        build_start = time.time()
        model_obj, λ, y, z = model.build_model(zones, configs, b, args.ambulances, args.periods, all_base_nodes)
        build_time = time.time() - build_start
        
        # Set parameters
        model_obj.setParam("TimeLimit", args.time_limit)
        model_obj.setParam("MIPGap", 0.01)
        
        # Solve
        model_obj, solve_time = model.solve()
        
        # Get results
        status = model_obj.status
        if status == 2:  # Optimal
            fairness_gap = int(z.X)
            solution_found = True
        else:
            fairness_gap = -1
            solution_found = False
        
        # Store results
        results.append({
            'config_size': num_configs,
            'build_time': build_time,
            'solve_time': solve_time,
            'total_time': build_time + solve_time,
            'fairness_gap': fairness_gap,
            'num_vars': model_obj.numVars,
            'num_constrs': model_obj.numConstrs,
            'status': status,
            'solution_found': solution_found
        })
        
        print(f"  ✅ Fairness gap: {fairness_gap}")
        print(f"  ⏱️ Build time: {build_time:.2f}s")
        print(f"  ⏱️ Solve time: {solve_time:.2f}s")
        print(f"  ⏱️ Total time: {build_time + solve_time:.2f}s")
        print(f"  📊 Model stats: {model_obj.numVars} vars, {model_obj.numConstrs} constraints")
    
    # Create and save summary DataFrame
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join(model_output_dir, "all_bases_analysis.csv"), index=False)    
    
    # Create visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(30, 8))
    
    # Plot 1: Total Time vs Configuration Size
    ax1.plot(results_df['config_size'], results_df['total_time'], 'o-', linewidth=2, markersize=8)
    ax1.set_xscale('log')
    ax1.set_xlabel('Number of Configurations', fontsize=14)
    ax1.set_ylabel('Total Runtime (seconds)', fontsize=14)
    ax1.set_title('Total Runtime vs Configuration Size (All Bases)', fontsize=16)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Build Time vs Optimize Time
    ax2.plot(results_df['config_size'], results_df['build_time'], 'o-', linewidth=2, markersize=8, label='Build Time')
    ax2.plot(results_df['config_size'], results_df['solve_time'], 's-', linewidth=2, markersize=8, label='Solve Time')
    ax2.set_xscale('log')
    ax2.set_xlabel('Number of Configurations', fontsize=14)
    ax2.set_ylabel('Time (seconds)', fontsize=14)
    ax2.set_title('Build Time vs Solve Time (All Bases)', fontsize=16)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Fairness Gap vs Configuration Size
    valid_gaps = results_df[results_df['fairness_gap'] >= 0]
    if not valid_gaps.empty:
        ax3.plot(valid_gaps['config_size'], valid_gaps['fairness_gap'], 'o-', linewidth=2, markersize=8, color='green')
        ax3.set_xscale('log')
        ax3.set_xlabel('Number of Configurations', fontsize=14)
        ax3.set_ylabel('Fairness Gap', fontsize=14)
        ax3.set_title('Fairness Gap vs Configuration Size (All Bases)', fontsize=16)
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(vis_output_dir, 'all_bases_analysis.png'), dpi=300, bbox_inches='tight')    
    
    # Clean up
    model.cleanup()
    
    print("\n✅ Analysis complete! Results saved to:")
    print(f"   - {os.path.join(model_output_dir, 'all_bases_analysis.csv')}")
    print(f"   - {os.path.join(vis_output_dir, 'all_bases_analysis.png')}")

if __name__ == "__main__":
    main()