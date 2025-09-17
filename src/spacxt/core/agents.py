
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Callable
import time
from .graph_store import SceneGraph, GraphPatch, Relation
from ..protocols.a2a_protocol import A2AMessage
from ..tools.topo_tool import relate_near

@dataclass
class Agent:
    id: str
    cls: str
    graph: SceneGraph
    send: Callable[[A2AMessage], None]
    inbox: List[A2AMessage]

    def perceive_and_propose(self):
        """Query neighbors and propose relations via A2A."""
        me = self.graph.get_node(self.id)
        if not me: return []
        neighbors = self.graph.neighbors(self.id, radius=1.5)
        msgs = []
        for nb in neighbors:
            rel = relate_near(me.__dict__, nb.__dict__)
            if rel["r"] == "near":
                msg = A2AMessage(
                    type="RELATION_PROPOSE",
                    sender=self.id,
                    receiver=nb.id,
                    payload={"relation": rel, "basis":"topo.relate_near"}
                )
                self.send(msg)
                msgs.append(msg)
        return msgs

    def handle_inbox(self) -> GraphPatch:
        patch = GraphPatch()
        while self.inbox:
            msg = self.inbox.pop(0)
            if msg.type == "RELATION_PROPOSE" and msg.receiver == self.id:
                rel = msg.payload["relation"]
                # Simple acceptance rule: accept if conf >= 0.6
                decision = "accept" if rel.get("conf",0) >= 0.6 else "reject"
                ack = A2AMessage(
                    type="RELATION_ACK",
                    sender=self.id,
                    receiver=msg.sender,
                    payload={"relation": rel, "decision": decision}
                )
                self.send(ack)
                if decision == "accept":
                    r = Relation(r=rel["r"], a=rel["a"], b=rel["b"], props=rel.get("props",{}), conf=rel.get("conf",1.0))
                    patch.add_relations.append(r)
            elif msg.type == "RELATION_ACK" and msg.receiver == self.id:
                # Could log / adjust confidence; in PoC we do nothing.
                pass
        return patch
