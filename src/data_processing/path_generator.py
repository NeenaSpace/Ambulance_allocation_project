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

from src.data_processing.data_loader import DataLoader

class PathGenerator:
    def __init__(self, data_dir, output_dir):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.data_loader = DataLoader(data_dir)
    
    def load_graph(self, instance, size):
        """Load graph from data files"""
        return self.data_loader.load_graph(instance, size)
    
    def load_bases(self, instance, size):
        """Load base stations"""
        return self.data_loader.load_bases(instance, size)
        
    def load_base(self, instance, size, base_idx):
        """Load a specific base station by index"""
        base_nodes = self.load_bases(instance, size)
        if base_idx < len(base_nodes):
            return base_nodes[base_idx]
        return None
    
    def generate_base_paths(self, G, base, periods):
        """Generate paths starting from a base"""
        # Implementation will depend on your existing code
        # This is a placeholder - replace with your actual implementation
        paths = []
        # Add code here to generate paths from base
        return paths
        
    def generate_paths(self, instance, periods, size):
        """Original method to maintain compatibility"""
        # Implementation of the original method
        pass
    
    def generate_paths_all_bases(self, instance, periods, size):
        """Generate ambulance paths considering all base stations together"""
        # Load graph
        G = self.load_graph(instance, size)
        
        # Load all base stations
        all_base_nodes = []
        # Assuming you have 5 bases (0-4) based on your scripts
        for base_idx in range(5):  
            base_node = self.load_base(instance, size, base_idx)
            if base_node:  # Only add if the base exists
                all_base_nodes.append(base_node)
        
        # Output directory for combined configurations
        output_dir = os.path.join(self.output_dir, str(size), f"{instance}-all_bases_t0_{periods-1}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate paths from all bases
        configs = []
        for base in all_base_nodes:
            # Generate paths starting from this base
            base_configs = self.generate_base_paths(G, base, periods)
            configs.extend(base_configs)
        
        # Save all configurations to a single file
        config_data = []
        for i, config in enumerate(configs):
            row = {}
            for t, (x, y) in enumerate(config):
                row[f"t{t}_x"] = x
                row[f"t{t}_y"] = y
            config_data.append(row)
        
        df = pd.DataFrame(config_data)
        df.to_csv(os.path.join(output_dir, "configs.csv"), index=False)
        
        print(f"Saved {len(configs)} configurations from all bases")

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
    
    # Generate paths using all bases combined
    generator = PathGenerator(args.data_dir, args.output_dir)
    
    # Modified to use all bases together instead of separately
    generator.generate_paths_all_bases(args.instance, args.periods, args.size)
    
    print(f"✅ Path generation complete for {args.instance} with {args.periods} time periods (all bases combined)")

if __name__ == "__main__":
    main()