import matplotlib.pyplot as plt
import networkx as nx
import os

def plot_network_with_bases(G, base_nodes, output_dir="./results/visualizations/network", filename=None):
    """
    Plot the network graph with base nodes highlighted
    
    Args:
        G: NetworkX graph
        base_nodes: List of base node coordinates
        output_dir: Directory to save the plot
        filename: Filename to save the plot (without extension)
    """
    # Color base nodes red, others light blue
    color_map = ['red' if node in base_nodes else 'lightblue' for node in G.nodes]
    
    # Build layout: use node coordinates as positions
    pos = {node: node for node in G.nodes}  # position = node coordinate
    
    # Create figure
    plt.figure(figsize=(10, 8))
    nx.draw(
        G, pos,
        with_labels=False,
        node_color=color_map,
        node_size=100,
        edge_color='gray',
    )
    
    # Add title
    title = f"Network Graph with {len(base_nodes)} Bases" if not filename else filename
    plt.title(title, fontsize=14)
    plt.axis('off')
    
    # Save figure if output_dir is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        if not filename:
            filename = f"network_with_{len(base_nodes)}_bases"
        plt.savefig(os.path.join(output_dir, f"{filename}.png"), bbox_inches='tight', dpi=300)
    
    return plt.gcf()

def plot_ambulance_allocation(allocation_data, t_periods, 
                              output_dir="./results/visualizations/analysis", 
                              filename="ambulance_allocation"):
    """
    Plot ambulance allocation over time
    
    Args:
        allocation_data: Dictionary of {zone: [allocations over time]}
        t_periods: Number of time periods
        output_dir: Directory to save the plot
        filename: Filename to save the plot (without extension)
    """
    plt.figure(figsize=(12, 8))
    
    for zone, allocations in allocation_data.items():
        if any(allocations):  # Only plot if there are any allocations for this zone
            plt.plot(range(t_periods), allocations, 'o-', label=f'Zone {zone}', linewidth=2, markersize=8)
    
    plt.xlabel('Time Period', fontsize=12)
    plt.ylabel('Number of Ambulances', fontsize=12)
    plt.title('Ambulance Allocation Over Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Save figure if output_dir is provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f"{filename}.png"), bbox_inches='tight', dpi=300)
    
    return plt.gcf()