#!/usr/bin/env python3
"""
Script to run model with consistency constraints using all bases
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
from src.models.consistency_model import ConsistencyModel
from src.visualization.coverage_plots import plot_coverage_analysis

def main():
    parser = argparse.ArgumentParser(description='Run model with consistency constraints using all bases')
    parser.add_argument('--instance', type=str, required=True, help='Instance name (e.g., 50-3004-6-7-35)')
    parser.add_argument('--periods', type=int, default=6, help='Number of time periods')
    parser.add_argument('--ambulances', type=int, default=50, help='Number of ambulances')
    parser.add_argument('--size', type=int, default=50, help='Graph size (nodes)')
    parser.add_argument('--num-configs', type=int, default=10000, help='Number of configurations to consider')
    parser.add_argument('--max-freq', type=int, default=3, help='Maximum frequency for configurations')
    parser.add_argument('--max-movement', type=int, default=10, help='Maximum movement between time periods')
    parser.add_argument('--time-limit', type=int, default=600, help='Time limit for optimization (seconds)')
    parser.add_argument('--data-dir', type=str, default='./data/raw', help='Directory containing raw data')
    parser.add_argument('--config-dir', type=str, default='./data/processed', help='Directory containing configurations')
    parser.add_argument('--results-dir', type=str, default='./results', help='Directory to save results')
    
    args = parser.parse_args()
    
    # Create results directories
    model_output_dir = os.path.join(args.results_dir, "model_outputs", "consistency")
    vis_output_dir = os.path.join(args.results_dir, "visualizations", "consistency")
    os.makedirs(model_output_dir, exist_ok=True)
    os.makedirs(vis_output_dir, exist_ok=True)
    
    # Load data
    loader = DataLoader(args.data_dir)
    G = loader.load_graph(args.instance, args.size)
    
    # Create cleaned adjacency dictionary
    adjacency_cleaned = {}
    for node, neighbors in G.adjacency():
        cleaned_node = loader.clean_coord(node)
        cleaned_neighbors = set()
        for neighbor in neighbors:
            cleaned_neighbors.add(loader.clean_coord(neighbor))
        adjacency_cleaned[cleaned_node] = cleaned_neighbors
    
    zones = [loader.clean_coord(node) for node in G.nodes]
    
    # Load configurations
    config_path = os.path.join(args.config_dir, str(args.size), 
                              f"{args.instance}-all_bases_t0_{args.periods-1}", 
                              "configs.csv")
    df = pd.read_csv(config_path).head(args.num_configs)
    
    configs = []
    for _, row in df.iterrows():
        cfg = []
        for t in range(args.periods):
            cfg.append(loader.clean_coord((row[f"t{t}_x"], row[f"t{t}_y"])))
        configs.append(cfg)
    
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
    
    model = ConsistencyModel(params, model_output_dir)
    model.initialize_environment()
    
    # Build and solve model
    print(f"\nSolving consistency model with {args.num_configs} configurations (all bases)...")
    start_time = time.time()
    
    # Load all base coordinates
    all_base_coords = []
    for base_idx in range(5):  # Assuming 5 bases (0-4)
        try:
            base_nodes = loader.load_bases(args.instance, args.size)
            if base_idx < len(base_nodes):
                base_coord = loader.clean_coord(base_nodes[base_idx])
                all_base_coords.append(base_coord)
        except Exception as e:
            print(f"Warning: Could not load base {base_idx}: {e}")
    
    print(f"Using {len(all_base_coords)} base stations: {all_base_coords}")

    model_obj, Z, q, x, m, y, z = model.build_model(
        zones, configs, adjacency_cleaned, args.ambulances, args.periods,
        args.max_freq, args.max_movement, all_base_coords
    )
    
    model_obj.setParam("TimeLimit", args.time_limit)
    model_obj.setParam("MIPGap", 0.01)
    
    model_obj.optimize()
    solve_time = time.time() - start_time
    
    # Print results
    print("\n=== MODEL STATISTICS ===")
    print(f"Number of Variables: {model_obj.numVars}")
    print(f"Number of Constraints: {model_obj.numConstrs}")
    print(f"Solve Time: {solve_time:.2f} seconds")
    
    if model_obj.status == 2:  # Optimal
        print(f"Fairness Gap: {z.X}")
        
        # Calculate coverage
        coverage_by_zone_time = {}
        for i in zones:
            for t in range(args.periods):
                # Check if zone i is covered at time t
                has_ambulances = x[i, t].X > 0.5
                neighbor_has_ambulances = False
                for j in adjacency_cleaned.get(i, set()):
                    if x[j, t].X > 0.5:
                        neighbor_has_ambulances = True
                        break
                coverage_by_zone_time[i, t] = 1 if (has_ambulances or neighbor_has_ambulances) else 0
        
        # Create visualization
        plot_coverage_analysis(
            coverage_by_zone_time, zones, args.periods, z.X,
            vis_output_dir, "complete_coverage_analysis_all_bases"
        )
        
        # Print coverage stats
        print("\n=== COVERAGE STATISTICS ===")
        for i in zones:
            total = sum(coverage_by_zone_time.get((i, t), 0) for t in range(args.periods))
            print(f"Zone {i}: Covered for {total} time periods")
        print(f"\nFairness Gap (max difference in coverage): {z.X}")

    status = model_obj.status
    result_saved = False
    if status == 2:  
        result_saved = True

    model.cleanup()

    print("\n✅ Analysis complete! Results saved to:")
    if result_saved:
        print(f"   - {os.path.join(vis_output_dir, 'complete_coverage_analysis_all_bases.png')}")

if __name__ == "__main__":
    main()