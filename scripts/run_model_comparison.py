#!/usr/bin/env python3
"""
Script to compare binary vs. original model formulations using all bases
"""

import os
import sys
import argparse
import time
import pandas as pd
import numpy as np

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing.data_loader import DataLoader
from src.models.base_model import BaseModel
from src.models.binary_model import BinaryModel
from src.visualization.model_comparison import plot_model_comparison

def main():
    parser = argparse.ArgumentParser(description='Compare binary vs. original model formulations using all bases')
    parser.add_argument('--instance', type=str, required=True, help='Instance name (e.g., 50-3004-6-7-35)')
    parser.add_argument('--periods', type=int, default=6, help='Number of time periods')
    parser.add_argument('--ambulances', type=int, default=50, help='Number of ambulances')
    parser.add_argument('--size', type=int, default=50, help='Graph size (nodes)')
    parser.add_argument('--config-sizes', type=str, default='100,500,1000,2000,5000', 
                        help='Comma-separated list of configuration sizes')
    parser.add_argument('--freq-bounds', type=str, default='3,5,10', 
                        help='Comma-separated list of maximum frequency bounds for binary model')
    parser.add_argument('--time-limit', type=int, default=600, help='Time limit for each optimization (seconds)')
    parser.add_argument('--data-dir', type=str, default='./data/raw', help='Directory containing raw data')
    parser.add_argument('--config-dir', type=str, default='./data/processed', help='Directory containing configurations')
    parser.add_argument('--results-dir', type=str, default='./results', help='Directory to save results')
    
    args = parser.parse_args()
    
    # Parse config sizes and frequency bounds
    config_sizes = [int(size) for size in args.config_sizes.split(',')]
    freq_bounds = [int(bound) for bound in args.freq_bounds.split(',')]
    
    # Create results directories
    model_output_dir = os.path.join(args.results_dir, "model_outputs", "comparison")
    vis_output_dir = os.path.join(args.results_dir, "visualizations", "comparison")
    os.makedirs(model_output_dir, exist_ok=True)
    os.makedirs(vis_output_dir, exist_ok=True)
    
    # Load data
    loader = DataLoader(args.data_dir)
    G = loader.load_graph(args.instance, args.size)
    
    # Create adjacency dictionary
    adjacency = {node: set(G.neighbors(node)) for node in G.nodes}
    zones = list(G.nodes)
    
    # Load all base nodes
    all_base_nodes = []
    for base_idx in range(5):  # Assuming 5 bases (0-4)
        try:
            base_nodes = loader.load_bases(args.instance, args.size)
            if base_idx < len(base_nodes):
                all_base_nodes.append(base_nodes[base_idx])
        except Exception as e:
            print(f"Warning: Could not load base {base_idx}: {e}")
    
    print(f"Using {len(all_base_nodes)} base stations")
    
    # Load configurations
    config_path = os.path.join(args.config_dir, str(args.size), 
                              f"{args.instance}-all_bases_t0_{args.periods-1}", 
                              "configs.csv")
    df_full = pd.read_csv(config_path)
    
    # Initialize models
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
    
    base_model = BaseModel(params, model_output_dir)
    binary_model = BinaryModel(params, model_output_dir)
    
    base_model.initialize_environment()
    binary_model.initialize_environment()
    
    # Run comparisons
    scaling_results = []
    
    for size in config_sizes:
        for freq_bound in freq_bounds:
            print(f"\nComparing models with size={size}, freq_bound={freq_bound}")
            
            # Use subset of configs
            df_subset = df_full.head(size)
            configs_subset = []
            for _, row in df_subset.iterrows():
                cfg = []
                for t in range(args.periods):
                    cfg.append((row[f"t{t}_x"], row[f"t{t}_y"]))
                configs_subset.append(cfg)
            
            # Build coverage matrix
            b_subset = {}
            for c_idx, config in enumerate(configs_subset):
                for t, zone in enumerate(config):
                    coverage = {zone} | adjacency.get(zone, set())
                    for z in coverage:
                        b_subset[z, t, c_idx] = 1
            
            # Original model
            print("  Solving original model...")
            start_orig = time.time()
            model_orig, λ, y, z = base_model.build_model(zones, configs_subset, b_subset, args.ambulances, args.periods, all_base_nodes)
            model_orig.setParam("TimeLimit", args.time_limit)
            model_orig.setParam("MIPGap", 0.01)
            model_orig.optimize()
            time_orig = time.time() - start_orig
            
            # Binary model
            print("  Solving binary model...")
            start_bin = time.time()
            model_bin, Z, q, y_bin, z_bin = binary_model.build_model(
                zones, configs_subset, b_subset, args.ambulances, args.periods, freq_bound, all_base_nodes
            )
            model_bin.setParam("TimeLimit", args.time_limit)
            model_bin.setParam("MIPGap", 0.01)
            model_bin.optimize()
            time_bin = time.time() - start_bin
            
            # Record results
            scaling_results.append({
                'config_size': size,
                'freq_bound': freq_bound,
                'orig_vars': model_orig.numVars,
                'bin_vars': model_bin.numVars,
                'orig_constrs': model_orig.numConstrs,
                'bin_constrs': model_bin.numConstrs,
                'orig_time': time_orig,
                'bin_time': time_bin,
                'orig_obj': model_orig.objVal if model_orig.status == 2 else -1,
                'bin_obj': model_bin.objVal if model_bin.status == 2 else -1
            })
            
            print(f"    ✅ Original model: {model_orig.objVal if model_orig.status == 2 else 'N/A'}, {time_orig:.2f}s")
            print(f"    ✅ Binary model: {model_bin.objVal if model_bin.status == 2 else 'N/A'}, {time_bin:.2f}s")
    
    # Create and save summary DataFrame
    scaling_df = pd.DataFrame(scaling_results)
    scaling_df.to_csv(os.path.join(model_output_dir, "binarization_comparison_all_bases.csv"), index=False)
    
    # Create visualization
    plot_model_comparison(scaling_df, vis_output_dir, "binarization_comparison_all_bases")
    
    # Clean up
    base_model.cleanup()
    binary_model.cleanup()
    
    print("\n✅ Comparison complete! Results saved to:")
    print(f"   - {os.path.join(model_output_dir, 'binarization_comparison_all_bases.csv')}")
    print(f"   - {os.path.join(vis_output_dir, 'binarization_comparison_all_bases.png')}")  

if __name__ == "__main__":
    main()