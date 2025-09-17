
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time, math, copy

@dataclass
class Node:
    id: str
    cls: str
    pos: Tuple[float, float, float]
    ori: Tuple[float, float, float, float]
    bbox: Dict[str, Any]
    aff: List[str] = field(default_factory=list)
    lom: str = "medium"
    conf: float = 1.0
    state: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Relation:
    r: str
    a: str
    b: str
    props: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=lambda: time.time())
    conf: float = 1.0

class GraphPatch:
    # CRDT-lite: adds/removes by id, last-write-wins on props with ts
    def __init__(self):
        self.add_nodes: Dict[str, Node] = {}
        self.update_nodes: Dict[str, Dict[str, Any]] = {}
        self.add_relations: List[Relation] = []
        self.remove_relations: List[Tuple[str,str,str]] = []  # (r,a,b)
    def to_dict(self):
        return {
            "add_nodes": {k: v.__dict__ for k,v in self.add_nodes.items()},
            "update_nodes": self.update_nodes,
            "add_relations": [r.__dict__ for r in self.add_relations],
            "remove_relations": self.remove_relations,
        }

class SceneGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.relations: Dict[Tuple[str,str,str], Relation] = {}
        self.events: List[Dict[str,Any]] = []  # event log

    def load_bootstrap(self, data: Dict[str,Any]):
        for obj in data["scene"]["objects"]:
            n = Node(
                id=obj["id"],
                cls=obj["cls"],
                pos=tuple(obj["pos"]),
                ori=tuple(obj["ori"]),
                bbox=obj["bbox"],
                aff=obj.get("aff",[]),
                lom=obj.get("lom","medium"),
                conf=obj.get("conf",1.0),
                state=obj.get("state",{})
            )
            self.nodes[n.id] = n
        for rel in data["scene"]["relations"]:
            key = (rel["r"], rel["a"], rel["b"])
            self.relations[key] = Relation(r=rel["r"], a=rel["a"], b=rel["b"], conf=rel.get("conf",1.0))
        self.events.append({"type":"BOOTSTRAP_LOADED","ts":time.time()})

    def get_node(self, nid: str) -> Optional[Node]:
        return self.nodes.get(nid)

    def neighbors(self, nid: str, radius: float=1.5) -> List[Node]:
        out = []
        me = self.nodes.get(nid)
        if not me: return out
        for other in self.nodes.values():
            if other.id == nid: continue
            d = math.dist(me.pos, other.pos)
            if d <= radius:
                out.append(other)
        return out

    def apply_patch(self, patch: GraphPatch):
        # add nodes
        for nid, node in patch.add_nodes.items():
            self.nodes[nid] = node
            self.events.append({"type":"NODE_ADDED","id":nid,"ts":time.time()})
        # update nodes
        for nid, upd in patch.update_nodes.items():
            n = self.nodes.get(nid)
            if not n: continue
            for k,v in upd.items():
                setattr(n, k, v)
            self.events.append({"type":"NODE_UPDATED","id":nid,"upd":upd,"ts":time.time()})
        # remove relations
        for key in patch.remove_relations:
            if key in self.relations:
                del self.relations[key]
                self.events.append({"type":"REL_REMOVED","key":key,"ts":time.time()})
        # add relations (LWW by ts)
        for rel in patch.add_relations:
            key = (rel.r, rel.a, rel.b)
            old = self.relations.get(key)
            if (old is None) or (rel.ts >= old.ts):
                self.relations[key] = rel
                self.events.append({"type":"REL_UPSERT","key":key,"ts":rel.ts,"conf":rel.conf})

    def as_llm_context(self, agent_pose=(1.0,1.5,1.6), roi="kitchen", K=6):
        # tiny summarizer: pick K nearest to agent_pose; compress repetitive items
        # (For demo, we don't cluster — keep it simple)
        objs = list(self.nodes.values())
        objs.sort(key=lambda n: math.dist(agent_pose, n.pos))
        top = objs[:K]
        # build summary
        notices = []
        if any(n.cls=="stove" and n.state.get("power")=="on" for n in top):
            notices.append("Stove is ON nearby.")
        summary = f"You are in {roi}. {len(top)} objects nearby."
        # relations filtered to those among top + roi ones
        rels = []
        topset = {n.id for n in top}
        for (r,a,b), obj in self.relations.items():
            if a in topset or b in topset:
                rels.append({"r":r,"a":a,"b":b,"conf":obj.conf})
        ctx = {
            "scene": {
                "frame": "map",
                "agent_pose": list(agent_pose) + [0,0,0,1],
                "roi": roi,
                "summary": summary,
                "objects": [{
                    "id": n.id, "cls": n.cls, "pos": list(n.pos),
                    "bbox": n.bbox, "lom": n.lom, "aff": n.aff,
                    "state": n.state, "conf": n.conf
                } for n in top],
                "relations": rels,
                "notices": notices
            }
        }
        return ctx
