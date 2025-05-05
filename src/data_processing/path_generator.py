import os
import pickle
import pandas as pd
import networkx as nx

class PathGenerator:
    def __init__(self, data_dir="./data/raw", output_dir="./data/processed"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        
    def generate_paths(self, instance_name, t_periods, size=50):
        """Generate all valid ambulance paths for all bases in an instance"""
        # Load graph
        with open(os.path.join(self.data_dir, str(size), f"{instance_name}.gpickle"), "rb") as f:
            G = pickle.load(f)
        neighbors_dict = {node: list(G.neighbors(node)) for node in G.nodes}
        
        # Load base coordinates
        with open(os.path.join(self.data_dir, str(size), f"{instance_name}.bases"), "r") as f:
            base_coords = [eval(line.strip()) for line in f if line.strip()]
        
        # Helper function for recursive path generation
        def generate_paths_recursive(current_path, steps_left, collected):
            if steps_left == 0:
                collected.append(current_path)
                return
            current_node = current_path[-1]
            if current_node in base_coords:
                for next_node in [current_node] + neighbors_dict.get(current_node, []):
                    generate_paths_recursive(current_path + [next_node], steps_left - 1, collected)
            else:
                generate_paths_recursive(current_path + [current_node], steps_left - 1, collected)
                
        
        # Generate paths for each base
        for idx, base in enumerate(base_coords):
            configurations = []
            generate_paths_recursive([base], t_periods - 1, configurations)
            
            # Create output dir
            out_dir = os.path.join(self.output_dir, str(size), f"{instance_name}-base{idx}_t0_{t_periods-1}")
            os.makedirs(out_dir, exist_ok=True)
            
            # Save as .pkl
            with open(os.path.join(out_dir, "configs.pkl"), "wb") as f:
                pickle.dump(configurations, f)
            
            # Save as .csv
            flat_configs = []
            for cfg_id, cfg in enumerate(configurations):
                flat = [cfg_id]
                for t in range(t_periods):
                    flat.extend(cfg[t])
                flat_configs.append(flat)
            
            columns = ["config_id"] + [f"t{t}_{axis}" for t in range(t_periods) for axis in ["x", "y"]]
            df = pd.DataFrame(flat_configs, columns=columns)
            df.to_csv(os.path.join(out_dir, "configs.csv"), index=False)
            
            print(f"✅ Base {idx}: saved {len(configurations)} configs to {out_dir}")