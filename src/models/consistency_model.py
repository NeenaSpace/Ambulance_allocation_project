import gurobipy as gp
from gurobipy import GRB
from .binary_model import BinaryModel

class ConsistencyModel(BinaryModel):
    def __init__(self, gurobi_params=None, results_dir="./results/model_outputs"):
        super().__init__(gurobi_params, results_dir)
    
    def build_model(self, 
                    zones, 
                    configs, 
                    adjacency, 
                    num_ambulances, 
                    t_periods,
                    max_config_frequency=3,
                    max_movement=10,
                    base_coords=None):
        """Build the binarized model with consistency constraints"""
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
        
        # x[i, t]: number of ambulances at zone i at time t
        x = {}
        for i in zones:
            for t in range(t_periods):
                x[i, t] = self.model.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{t}")
        
        # m[i, j, t]: number of ambulances moving from zone i to j at time t
        m = {}
        for t in range(t_periods-1):
            for i in zones:
                for j in zones:
                    if i == j or j in adjacency.get(i, set()):
                        m[i, j, t] = self.model.addVar(vtype=GRB.INTEGER, name=f"m_{i}_{j}_{t}")
        
        y = self.model.addVars(zones, vtype=GRB.INTEGER, name="y")
        z = self.model.addVar(vtype=GRB.INTEGER, name="z")
        
        self.model.update()
        
        # Constraints
        # only base_coords can have ambulances at time 0
        if base_coords:
            for i in zones:
                if i not in base_coords:  
                    self.model.addConstr(x[i, 0] == 0, f"no_ambulance_at_nonbase_{i}_0")            
        # One-hot constraint
        for c in range(len(configs)):
            self.model.addConstr(
                gp.quicksum(Z[c, k] for k in range(max_config_frequency + 1)) == 1,
                f"one_hot_{c}"
            )
        
        # Link q to Z
        for c in range(len(configs)):
            self.model.addConstr(
                q[c] == gp.quicksum(k * Z[c, k] for k in range(max_config_frequency + 1)),
                f"link_q_{c}"
            )
        
        # Total ambulance count
        self.model.addConstr(
            gp.quicksum(q[c] for c in range(len(configs))) == num_ambulances,
            "ambulance_count"
        )
        
        # Calculate x[i,t]
        for i in zones:
            for t in range(t_periods):
                contributions = []
                for c, config in enumerate(configs):
                    if config[t] == i:
                        contributions.append(q[c])
                
                if contributions:
                    self.model.addConstr(
                        x[i, t] == gp.quicksum(contributions),
                        f"ambulance_count_{i}_{t}"
                    )
                else:
                    self.model.addConstr(x[i, t] == 0, f"ambulance_count_{i}_{t}")
        
        # Flow conservation
        for t in range(t_periods-1):
            for i in zones:
                leaving = gp.quicksum(m[i, j, t] for j in zones if (i, j, t) in m)
                arriving = gp.quicksum(m[j, i, t] for j in zones if (j, i, t) in m)
                self.model.addConstr(
                    x[i, t] + arriving - leaving == x[i, t+1],
                    f"flow_conservation_{i}_{t}"
                )
        
        # Movement constraints
        for t in range(t_periods-1):
            total_movement = gp.quicksum(m[i, j, t] for (i, j, t_) in m if t_ == t and i != j)
            self.model.addConstr(
                total_movement <= max_movement,
                f"max_movement_{t}"
            )
        
        # Adjacency constraints
        for t in range(t_periods-1):
            for i in zones:
                for j in zones:
                    if i != j and j not in adjacency.get(i, set()):
                        if (i, j, t) in m:
                            self.model.addConstr(m[i, j, t] == 0, f"adjacent_{i}_{j}_{t}")
        
        # Coverage calculation for fairness
        # We calculate coverage based on configurations selected
        b = {}  # Coverage matrix to be calculated based on configs
        for c_idx, config in enumerate(configs):
            for t, zone in enumerate(config):
                coverage = {zone} | adjacency.get(zone, set())
                for z_loc in coverage:
                    b[z_loc, t, c_idx] = 1
        
        # Coverage constraints
        for i in zones:
            self.model.addConstr(
                y[i] == gp.quicksum(
                    b.get((i, t, c), 0) * q[c] 
                    for c in range(len(configs)) 
                    for t in range(t_periods)
                ),
                f"coverage_{i}"
            )
        
        # Fairness constraints
        for i in zones:
            for j in zones:
                self.model.addConstr(z >= y[i] - y[j], f"fair_{i}_{j}")
        
        # Objective
        self.model.setObjective(z, GRB.MINIMIZE)
        
        return self.model, Z, q, x, m, y, z