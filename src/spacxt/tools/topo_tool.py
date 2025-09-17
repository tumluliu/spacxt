
from typing import List, Dict, Any, Tuple
import math

def dist(a: Tuple[float,float,float], b: Tuple[float,float,float]) -> float:
    return math.dist(a,b)

def relate_near(node_a: Dict[str,Any], node_b: Dict[str,Any], near_thresh: float=0.75) -> Dict[str,Any]:
    d = dist(tuple(node_a["pos"]), tuple(node_b["pos"]))
    conf = max(0.0, min(1.0, 1.0 - (d/near_thresh))) if d < near_thresh*2 else 0.1
    rel = None
    if d <= near_thresh:
        rel = {"r":"near","a":node_a["id"],"b":node_b["id"],"props":{"dist":d},"conf":conf}
    else:
        rel = {"r":"far","a":node_a["id"],"b":node_b["id"],"props":{"dist":d},"conf":1.0-conf}
    return rel

def visible_from(agent_pose, node: Dict[str,Any]) -> bool:
    # Placeholder: always true in PoC
    return True
