#!/usr/bin/env python3
"""
Script to prepare data and generate configurations from all bases together
"""

import os
import sys
import argparse
import pandas as pd

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing.path_generator import PathGenerator
from src.data_processing.data_loader import DataLoader

def main():
    parser = argparse.ArgumentParser(description='Generate ambulance path configurations')
    parser.add_argument('--instance', type=str, required=True, help='Instance name (e.g., 50-3004-6-7-35)')
    parser.add_argument('--periods', type=int, default=6, help='Number of time periods')
    parser.add_argument('--size', type=int, default=50, help='Graph size (nodes)')
    parser.add_argument('--data-dir', type=str, default='./data/raw', help='Directory containing raw data')
    parser.add_argument('--output-dir', type=str, default='./data/processed', help='Directory to save output')
    parser.add_argument('--bases-only', action='store_true', default=True, 
                    help='Only deploy ambulances at base stations')
    parser.add_argument('--num-ambulances', type=int, default=10, 
                    help='Number of ambulances to deploy')

    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(os.path.join(args.output_dir, str(args.size)), exist_ok=True)
    
    # Generate individual base paths first if they don't exist
    generator = PathGenerator(args.data_dir, args.output_dir)
    generator.generate_paths(args.instance, args.periods, args.size)
    
    # Now combine all base configurations into a single file
    loader = DataLoader(args.data_dir)
    df_list = []
    
    for base_idx in range(5):  # Assuming 5 bases (0-4)
        config_path = os.path.join(args.output_dir, str(args.size), 
                                  f"{args.instance}-base{base_idx}_t0_{args.periods-1}", 
                                  "configs.csv")
        try:
            df_base = pd.read_csv(config_path)
            df_list.append(df_base)
            print(f"Loaded configurations from base {base_idx}")
        except FileNotFoundError:
            print(f"Warning: No configurations found for base {base_idx}")

    if not df_list:
        raise ValueError("No configuration files found for any base")

    # Combine all configurations into a single DataFrame
    df_full = pd.concat(df_list, ignore_index=True)
    
    # Create the all_bases directory and save the combined configurations
    all_bases_dir = os.path.join(args.output_dir, str(args.size), 
                               f"{args.instance}-all_bases_t0_{args.periods-1}")
    os.makedirs(all_bases_dir, exist_ok=True)
    
    df_full.to_csv(os.path.join(all_bases_dir, "configs.csv"), index=False)
    
    print(f"✅ Path generation complete for {args.instance} with {args.periods} time periods")
    print(f"✅ Combined {len(df_full)} configurations from all bases to {all_bases_dir}/configs.csv")

if __name__ == "__main__":
    main()