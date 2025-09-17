
from typing import Dict, List, Callable
from collections import defaultdict
from .graph_store import SceneGraph
from .agents import Agent
from ..protocols.a2a_protocol import A2AMessage

class Bus:
    def __init__(self):
        self.queues: Dict[str, List[A2AMessage]] = defaultdict(list)
    def send(self, msg: A2AMessage):
        self.queues[msg.receiver].append(msg)
    def drain(self, agent_id: str):
        msgs = self.queues[agent_id]
        self.queues[agent_id] = []
        return msgs

def make_agents(graph: SceneGraph, bus: Bus, ids: List[str]) -> Dict[str, Agent]:
    agents = {}
    for nid in ids:
        node = graph.get_node(nid)
        if not node: continue
        a = Agent(
            id=nid, cls=node.cls, graph=graph,
            send=bus.send, inbox=[]
        )
        agents[nid] = a
    return agents

def tick(graph: SceneGraph, bus: Bus, agents: Dict[str, Agent]):
    # 1) deliver messages
    for aid, ag in agents.items():
        ag.inbox.extend(bus.drain(aid))
    # 2) agents perceive & propose
    for ag in agents.values():
        ag.perceive_and_propose()
    # 3) agents handle inbox -> patches
    for ag in agents.values():
        patch = ag.handle_inbox()
        if patch.add_relations or patch.update_nodes or patch.add_nodes or patch.remove_relations:
            graph.apply_patch(patch)
