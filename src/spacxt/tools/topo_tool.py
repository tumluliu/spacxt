
from typing import List, Dict, Any, Tuple
import math

def dist(a: Tuple[float,float,float], b: Tuple[float,float,float]) -> float:
    return math.dist(a,b)

def relate_near(node_a: Dict[str,Any], node_b: Dict[str,Any], near_thresh: float=0.8) -> Dict[str,Any]:
    d = dist(tuple(node_a["pos"]), tuple(node_b["pos"]))

    if d <= near_thresh:
        # For "near": Use a simple confidence that's always above acceptance threshold
        # Very close (d < thresh/2) = high confidence (0.9)
        # Close (d <= thresh) = medium-high confidence (0.7)
        if d < near_thresh / 2:
            conf = 0.9
        else:
            conf = 0.7
        rel = {"r":"near","a":node_a["id"],"b":node_b["id"],"props":{"dist":d},"conf":conf}
    else:
        # For "far": reasonable confidence for distant objects
        conf = min(0.8, 0.3 + (d/near_thresh - 1.0) * 0.2)
        rel = {"r":"far","a":node_a["id"],"b":node_b["id"],"props":{"dist":d},"conf":conf}
    return rel

def visible_from(agent_pose, node: Dict[str,Any]) -> bool:
    # Placeholder: always true in PoC
    return True
