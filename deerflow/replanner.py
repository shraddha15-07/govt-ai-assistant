# deerflow/replanner.py
# DeerFlow Dynamic Workflow Replanning
# Changes the plan automatically when problems are detected
# Like Google Maps recalculating route when there is traffic

import datetime

class WorkflowNode:
    """One step in the workflow plan"""
    def __init__(self, name, agent, has_condition=False):
        self.name          = name
        self.agent         = agent
        self.has_condition = has_condition
        self.executed      = False
        self.inserted      = False  # was this added by replanner?

def build_default_graph():
    """
    Build the standard 4-step workflow graph
    This is the normal plan when everything is clear
    """
    return [
        WorkflowNode("n1", "planner",    False),
        WorkflowNode("n2", "analysis",   False),
        WorkflowNode("n3", "drafting",   False),
        WorkflowNode("n4", "compliance", True),
    ]

def replan_workflow(graph, state, after_node="n2"):
    """
    DeerFlow replanning engine
    Inserts extra steps when ambiguities or problems detected
    Returns updated graph and list of what was inserted
    """
    inserted = []

    # If no graph exists build default
    if graph is None:
        graph = build_default_graph()

    ambiguities  = getattr(state, "ambiguities",       [])
    errors       = getattr(state, "error_log",         [])
    contradictions = getattr(state, "contradictions",  [])
    fallback     = getattr(state, "fallback_triggered", False)

    # Replan 1: ambiguities detected → insert clarification step
    if ambiguities and not any(
        n.name == "clarification" for n in graph
    ):
        node = WorkflowNode("clarification", "analysis", True)
        node.inserted = True
        _insert_after(graph, after_node, node)
        inserted.append("clarification_step")
        print(f"  [DeerFlow] Inserted clarification step "
              f"({len(ambiguities)} ambiguities)")

    # Replan 2: errors detected → insert fallback step
    if (errors or fallback) and not any(
        n.name == "fallback" for n in graph
    ):
        node = WorkflowNode("fallback", "planner", True)
        node.inserted = True
        _insert_after(graph, "n1", node)
        inserted.append("fallback_handling_step")
        print(f"  [DeerFlow] Inserted fallback step")

    # Replan 3: contradictions detected → insert comparison step
    if contradictions and not any(
        n.name == "contradiction_check" for n in graph
    ):
        node = WorkflowNode("contradiction_check", "analysis", True)
        node.inserted = True
        _insert_after(graph, "n2", node)
        inserted.append("contradiction_check_step")
        print(f"  [DeerFlow] Inserted contradiction check "
              f"({len(contradictions)} found)")

    return graph, inserted


def _insert_after(graph, after_name, new_node):
    """Helper: insert a node after a named node"""
    for i, node in enumerate(graph):
        if node.name == after_name:
            graph.insert(i + 1, new_node)
            return
    graph.append(new_node)


def graph_to_dict(graph):
    """Convert graph to list of dicts for saving to JSON"""
    return [
        {
            "name":          n.name,
            "agent":         n.agent,
            "has_condition": n.has_condition,
            "executed":      n.executed,
            "inserted":      n.inserted
        }
        for n in graph
    ]