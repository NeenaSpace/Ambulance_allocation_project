import gurobipy as gp
from gurobipy import GRB
import time
import os
import json

class BaseModel:
    def __init__(self, 
                 gurobi_params=None, 
                 results_dir="./results/model_outputs"):
        self.params = gurobi_params if gurobi_params else {}
        self.results_dir = results_dir
        self.env = None
        self.model = None
        
    def initialize_environment(self):
        """Initialize Gurobi environment with license parameters"""
        self.env = gp.Env(params=self.params)
        self.model = gp.Model(env=self.env)
        return self.model
    
    def build_model(self, 
                zones, 
                configs, 
                coverage_matrix, 
                num_ambulances, 
                t_periods,
                all_base_nodes=None): 
        """Build the basic ILP model with binary selection variables"""
        # Reset model
        if self.model:
            self.model.dispose()
        self.model = gp.Model(env=self.env)
        
        # Variables
        λ = self.model.addVars(len(configs), vtype=GRB.BINARY, name="lambda")
        y = self.model.addVars(zones, vtype=GRB.INTEGER, name="y")
        z = self.model.addVar(vtype=GRB.INTEGER, name="z")
        
        if all_base_nodes is not None:
            valid_configs = []
            for i, config in enumerate(configs):
                if config[0] in all_base_nodes:  
                    valid_configs.append(i)
            
            if valid_configs:
                self.model.addConstr(
                    gp.quicksum(λ[c] for c in range(len(configs)) if c not in valid_configs) == 0,
                    "all_bases_constraint" 
                )
            
        # Constraints
        # 1. Select exactly num_ambulances configs
        self.model.addConstr(
            gp.quicksum(λ[c] for c in range(len(configs))) == num_ambulances, 
            "ambulance_count"
        )
        
        # 2. Define y_i = total coverage for each zone
        for i in zones:
            self.model.addConstr(
                y[i] == gp.quicksum(
                    coverage_matrix.get((i, t, c), 0) * λ[c] 
                    for c in range(len(configs)) 
                    for t in range(t_periods)
                ),
                f"coverage_{i}"
            )
        
        # 3. Fairness constraint: z ≥ y_i - y_j
        for i in zones:
            for j in zones:
                self.model.addConstr(z >= y[i] - y[j], f"fair_{i}_{j}")
        
        # Objective
        self.model.setObjective(z, GRB.MINIMIZE)
        
        return self.model, λ, y, z
    
    def solve(self, time_limit=None, gap=None):
        """Solve the model with optional time limit and gap"""
        if time_limit:
            self.model.setParam("TimeLimit", time_limit)
        if gap:
            self.model.setParam("MIPGap", gap)
            
        start_time = time.time()
        self.model.optimize()
        solve_time = time.time() - start_time
        
        return self.model, solve_time
    
    def save_results(self, name, base_idx, num_configs):
        """Save model results to file"""
        output_dir = os.path.join(self.results_dir, f"base{base_idx}")
        os.makedirs(output_dir, exist_ok=True)
        
        result_file = os.path.join(output_dir, f"{name}_{num_configs}.json")
        
        result = {
            "status": self.model.status,
            "objective": self.model.objVal if self.model.status == GRB.OPTIMAL else None,
            "runtime": self.model.Runtime,
            "num_vars": self.model.numVars,
            "num_constrs": self.model.numConstrs,
            "gap": self.model.MIPGap
        }
        
        with open(result_file, 'w') as f:
            json.dump(result, f)
            
        return result
    
    def cleanup(self):
        """Dispose of Gurobi model and environment"""
        if self.model:
            self.model.dispose()
        if self.env:
            self.env.dispose()