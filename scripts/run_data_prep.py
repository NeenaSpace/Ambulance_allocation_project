#!/usr/bin/env python3
"""
Script to prepare data and generate configurations
"""

import os
import sys
import argparse

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing.path_generator import PathGenerator

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
    
    # Generate paths
    generator = PathGenerator(args.data_dir, args.output_dir)
    generator.generate_paths(args.instance, args.periods, args.size)
    
    print(f"✅ Path generation complete for {args.instance} with {args.periods} time periods")

if __name__ == "__main__":
    main()