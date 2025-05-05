import gurobipy as gp
from gurobipy import GRB
from .base_model import BaseModel

class BinaryModel(BaseModel):
    def __init__(self, gurobi_params=None, results_dir="./results/model_outputs"):
        super().__init__(gurobi_params, results_dir)
        
    def build_model(self, 
                zones, 
                configs, 
                coverage_matrix, 
                num_ambulances, 
                t_periods,
                max_config_frequency=5,
                base_nodes=None):  
        """Build the binarized ILP model with unary expansion of integers"""
        # Reset model
        if self.model:
            self.model.dispose()
        self.model = gp.Model(env=self.env)
        
        # Variables
        # Z[c, k]: binary variable indicating if configuration c occurs k times
        Z = {}
        for c in range(len(configs)):
            for k in range(max_config_frequency + 1):
                Z[c, k] = self.model.addVar(vtype=GRB.BINARY, name=f"Z_{c}_{k}")
        
        # q[c]: integer variable representing how many times configuration c occurs
        q = self.model.addVars(len(configs), vtype=GRB.INTEGER, name="q")
        
        y = self.model.addVars(zones, vtype=GRB.INTEGER, name="y")
        z = self.model.addVar(vtype=GRB.INTEGER, name="z")
        
        #  add base_nodes constraint
        if base_nodes is not None:
            valid_configs = []
            for i, config in enumerate(configs):
                if config[0] in base_nodes:  
                    valid_configs.append(i)
            
            if valid_configs:
                self.model.addConstr(
                    gp.quicksum(q[c] for c in range(len(configs)) if c not in valid_configs) == 0,
                    "base_only_constraint"
                )
        
        # Constraints
        # One-hot constraint: Each configuration occurs exactly once with some frequency
        for c in range(len(configs)):
            self.model.addConstr(
                gp.quicksum(Z[c, k] for k in range(max_config_frequency + 1)) == 1,
                f"one_hot_{c}"
            )
        
        # Link q to Z: q[c] = sum(k * Z[c,k])
        for c in range(len(configs)):
            self.model.addConstr(
                q[c] == gp.quicksum(k * Z[c, k] for k in range(max_config_frequency + 1)),
                f"link_q_{c}"
            )
        
        # Total ambulance count constraint
        self.model.addConstr(
            gp.quicksum(q[c] for c in range(len(configs))) == num_ambulances,
            "ambulance_count_binarized"
        )
        
        # Coverage constraints
        for i in zones:
            self.model.addConstr(
                y[i] == gp.quicksum(
                    coverage_matrix.get((i, t, c), 0) * q[c] 
                    for c in range(len(configs)) 
                    for t in range(t_periods)
                ),
                f"coverage_binarized_{i}"
            )
        
        # Fairness constraints
        for i in zones:
            for j in zones:
                self.model.addConstr(z >= y[i] - y[j], f"fair_binarized_{i}_{j}")
        
        # Objective
        self.model.setObjective(z, GRB.MINIMIZE)
        
        return self.model, Z, q, y, z