import os
import pickle
import pandas as pd
import networkx as nx

class DataLoader:
    def __init__(self, data_dir="./data/raw"):
        self.data_dir = data_dir
        
    def load_graph(self, instance_name, size=50):
        """Load a graph instance from a .gpickle file"""
        file_path = os.path.join(self.data_dir, str(size), f"{instance_name}.gpickle")
        
        with open(file_path, 'rb') as f:
            G = pickle.load(f)
            
        if not isinstance(G, nx.Graph):
            raise ValueError(f"{instance_name}: Not a valid NetworkX graph.")
            
        return G
    
    def load_bases(self, instance_name, size=50):
        """Load base coordinates from a .bases file"""
        file_path = os.path.join(self.data_dir, str(size), f"{instance_name}.bases")
        
        base_coords = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    coord = eval(line.strip())  # assumes format: (x, y)
                    base_coords.append(coord)
                    
        return base_coords
    
    def load_configurations(self, instance_name, base_idx, t_periods, size=50):
        """Load generated configurations for a base"""
        config_dir = f"./data/processed/{size}"
        config_path = os.path.join(config_dir, f"{instance_name}-base{base_idx}_t0_{t_periods-1}", "configs.csv")
        
        return pd.read_csv(config_path)
    
    def clean_coord(self, node):
        """Clean node coordinates to prevent float precision issues"""
        return tuple(round(float(coord), 6) for coord in node)