# Ambulance Allocation Optimization

This project implements optimization models for fair ambulance allocation across zones over multiple time periods.

## Project Structure

```
ambulance-allocation/
├── data/                       # Raw and processed data
│   ├── raw/                    # Original data files
│   │   ├── 50/                 # 50-node instances
│   │   ├── 100/                # 100-node instances
│   │   └── 200/                # 200-node instances
│   └── processed/              # Generated configurations
│       └── 50/                 # Generated paths for 50-node instances
├── src/                        # Source code
│   ├── data_processing/        # Data loading and preprocessing
│   │   ├── __init__.py
│   │   ├── data_loader.py      # Functions to load graph data
│   │   └── path_generator.py   # Code for generating ambulance paths
│   ├── models/                 # Optimization models
│   │   ├── __init__.py
│   │   ├── base_model.py       # Base ILP model
│   │   ├── binary_model.py     # Model with binary variables
│   │   └── consistency_model.py # Model with consistency constraints
│   └── visualization/          # Plotting and visualization
│       ├── __init__.py
│       ├── graph_plots.py      # Network visualization
│       ├── model_comparison.py # Comparison plots
│       └── coverage_plots.py   # Coverage analysis plots
├── results/                    # Results storage
│   ├── model_outputs/          # Saved model results
│   │   ├── all_bases/          # Results for all bases combined
│   │   └── comparison/         # Model comparison results
│   └── visualizations/         # Generated plots and charts
│       ├── analysis/           # Base analysis visualizations
│       ├── comparison/         # Model comparison visualizations
│       └── consistency/        # Consistency model visualizations
├── scripts/                    # Executable scripts
│   ├── run_data_prep.py        # Script to prepare data
│   ├── run_base_analysis.py    # Script to run base analysis
│   ├── run_model_comparison.py # Script to compare models
│   └── run_consistency.py      # Script to run with consistency
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Getting Started

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Generate path configurations using all bases:
```bash
python3 scripts/run_data_prep.py --instance 50-3004-6-7-35 --periods 6 --size 50
```

## Running the Ambulance Allocation Models

This project provides several scripts to analyze ambulance allocations with all bases considered together and different model configurations.

### Base Analysis (All-Bases Model)

Run this command to analyze all base stations together with the base-only constraint (ambulances can only be deployed from base stations):

```bash
python3 scripts/run_base_analysis.py --instance 50-3004-6-7-35 --min-configs 100 --max-configs 1000 --num-steps 4 --ambulances 50
```

### Model Comparison

Compare different model formulations (original vs. binary formulation) using all bases:

```bash
python3 scripts/run_model_comparison.py --instance 50-3004-6-7-35 --config-sizes 100,500,1000 --freq-bounds 3,5 --ambulances 50
```

### Consistency Model

Run the model with consistency constraints that ensure ambulances can only be deployed from base stations initially, but can move to any zone in subsequent time periods:

```bash
python3 scripts/run_consistency.py --instance 50-3004-6-7-35 --num-configs 1000 --max-freq 3 --max-movement 10 --ambulances 50
```

## Parameters Explanation

- `--instance`: The instance name (e.g., 50-3004-6-7-35)
- `--periods`: Number of time periods (default: 6)
- `--ambulances`: Number of ambulances to deploy (default: 35, recommended: 50)
- `--size`: Graph size in nodes (default: 50)
- `--min-configs`: Minimum number of configurations to test
- `--max-configs`: Maximum number of configurations to test
- `--num-steps`: Number of logarithmic steps between min and max configs
- `--config-sizes`: Comma-separated list of configuration sizes for comparison
- `--freq-bounds`: Comma-separated list of maximum frequency bounds for binary model
- `--max-movement`: Maximum movement allowed between time periods
- `--time-limit`: Time limit for optimization in seconds (default: 600)

## Output Locations

The results from these commands will be saved to the following locations:

- **Base Analysis Results**: 
  - CSV file: `results/model_outputs/all_bases/all_bases_analysis.csv`
  - Visualization: `results/visualizations/analysis/all_bases_analysis.png`

- **Model Comparison Results**:
  - CSV file: `results/model_outputs/comparison/binarization_comparison_all_bases.csv`
  - Visualization: `results/visualizations/comparison/binarization_comparison_all_bases.png`

- **Consistency Model Results**:
  - Visualization: `results/visualizations/consistency/complete_coverage_analysis_all_bases.png`

## Key Modifications

Several key modifications were made to the original approach:

1. **All-Bases Approach**: Instead of analyzing each base station separately, we now consider all base stations together. This provides a more realistic model of ambulance allocation across the entire network.

2. **Base Station Constraint**: We modified the model to only allow deployment from base stations, which is more realistic than allowing deployment from any zone.

3. **Initial-Time Restriction**: In the consistency model, we initially required ambulances to be at base stations at all time periods, but this proved infeasible. We relaxed this constraint to require ambulances to be at base stations only at the initial time period (t=0).

4. **Ambulance Count**: We increased the ambulance count from 35 to 50 to ensure feasible solutions with the base station constraint.

5. **File Naming**: Naming conventions now use "all_bases" instead of "base{N}" to reflect the combined base approach.

## Optimization Models

The project includes three main optimization models:

1. **Base Model**: Basic ILP formulation with binary selection variables.
2. **Binary Model**: Binarized version using unary expansion of integer variables.
3. **Consistency Model**: Extended model with constraints on ambulance movement between time periods.

## License

This project includes code that uses Gurobi, which requires a license to run. Make sure to place your `gurobi.lic` file in the `data/raw/` directory.