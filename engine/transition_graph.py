"""Voynich OS transition-graph utilities (public-safe).

Provides a helper to convert the VM output into a simple
NetworkX directed graph for further analysis or visualization.
"""

from typing import Dict, Any
import networkx as nx

def vm_output_to_nx(vm_output: Dict[str, Any]) -> nx.DiGraph:
    """Convert a VM graph dict (nodes/edges) into a NetworkX DiGraph."""
    g = nx.DiGraph()

    for node in vm_output.get("nodes", []):
        node_id = node["id"]
        g.add_node(node_id, **{k: v for k, v in node.items() if k != "id"})

    for edge in vm_output.get("edges", []):
        src = edge["source"]
        tgt = edge["target"]
        g.add_edge(src, tgt)

    return g

