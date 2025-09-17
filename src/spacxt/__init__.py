"""
SpacXT - Spatial Context Engine with Agentized Objects

A minimal runnable prototype for 3D Scene Graph with agent-based spatial reasoning.
"""

__version__ = "0.1.0"

from .core.graph_store import SceneGraph, Node, Relation, GraphPatch
from .core.agents import Agent
from .core.orchestrator import Bus, make_agents, tick
from .protocols.a2a_protocol import A2AMessage
from .tools.topo_tool import relate_near

__all__ = [
    "SceneGraph",
    "Node",
    "Relation",
    "GraphPatch",
    "Agent",
    "Bus",
    "make_agents",
    "tick",
    "A2AMessage",
    "relate_near",
]
