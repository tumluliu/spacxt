
from typing import List, Dict, Any, Tuple, Optional
import math

def dist(a: Tuple[float,float,float], b: Tuple[float,float,float]) -> float:
    return math.dist(a,b)

def detect_spatial_relation(node_a: Dict[str,Any], node_b: Dict[str,Any]) -> Dict[str,Any]:
    """Detect the most appropriate spatial relation between two objects."""

    # Get positions and sizes
    pos_a = tuple(node_a["pos"])
    pos_b = tuple(node_b["pos"])
    size_a = node_a["bbox"]["xyz"]
    size_b = node_b["bbox"]["xyz"]

    # Calculate 3D distance
    d = dist(pos_a, pos_b)

    # Calculate 2D distance (ignoring height)
    d_2d = math.sqrt((pos_a[0] - pos_b[0])**2 + (pos_a[1] - pos_b[1])**2)

    # Height difference
    height_diff = abs(pos_a[2] - pos_b[2])

    # Check for "on_top_of" relation (A on top of B)
    on_top_relation = check_on_top_of(pos_a, size_a, pos_b, size_b)
    if on_top_relation:
        return on_top_relation

    # Check for "supports" relation (A supports B, i.e., B on top of A)
    supports_relation = check_on_top_of(pos_b, size_b, pos_a, size_a)
    if supports_relation:
        # Create support relation (A supports B)
        return {
            "r": "supports",
            "a": node_a["id"],  # A supports B
            "b": node_b["id"],
            "props": {
                "height_diff": pos_b[2] - pos_a[2],
                "x_offset": pos_b[0] - pos_a[0],
                "y_offset": pos_b[1] - pos_a[1]
            },
            "conf": supports_relation["conf"]
        }

    # Check for "beside" relation (close in 2D, similar height)
    beside_relation = check_beside(pos_a, size_a, pos_b, size_b, d_2d, height_diff)
    if beside_relation:
        return beside_relation

    # Check for "above/below" relation
    above_below_relation = check_above_below(pos_a, size_a, pos_b, size_b, d_2d, height_diff)
    if above_below_relation:
        return above_below_relation

    # Default to distance-based relations (near/far)
    return relate_distance(node_a, node_b, d)

def check_on_top_of(pos_a: Tuple[float,float,float], size_a: List[float],
                   pos_b: Tuple[float,float,float], size_b: List[float]) -> Optional[Dict[str,Any]]:
    """Check if object A is on top of object B."""

    # Check if A is above B
    if pos_a[2] <= pos_b[2]:
        return None

    # Check if A is roughly above B in X-Y plane
    x_overlap = abs(pos_a[0] - pos_b[0]) <= (size_b[0]/2 + size_a[0]/4)
    y_overlap = abs(pos_a[1] - pos_b[1]) <= (size_b[1]/2 + size_a[1]/4)

    if not (x_overlap and y_overlap):
        return None

    # Check if A is at the right height to be "on" B
    expected_height = pos_b[2] + size_b[2]/2 + size_a[2]/2
    height_tolerance = 0.15  # 15cm tolerance

    if abs(pos_a[2] - expected_height) <= height_tolerance:
        confidence = 0.95 - (abs(pos_a[2] - expected_height) / height_tolerance) * 0.2
        return {
            "r": "on_top_of",
            "a": pos_a,  # Will be replaced with actual IDs by caller
            "b": pos_b,
            "props": {
                "height_diff": pos_a[2] - pos_b[2],
                "x_offset": pos_a[0] - pos_b[0],
                "y_offset": pos_a[1] - pos_b[1]
            },
            "conf": max(0.7, confidence)
        }

    return None

def check_beside(pos_a: Tuple[float,float,float], size_a: List[float],
                pos_b: Tuple[float,float,float], size_b: List[float],
                d_2d: float, height_diff: float) -> Optional[Dict[str,Any]]:
    """Check if objects are beside each other."""

    # Objects should be at similar heights
    if height_diff > 0.3:  # 30cm height difference tolerance
        return None

    # Objects should be close in 2D
    max_beside_distance = (max(size_a[0], size_a[1]) + max(size_b[0], size_b[1])) / 2 + 0.4

    if d_2d <= max_beside_distance:
        confidence = 0.85 - (height_diff / 0.3) * 0.15  # Reduce confidence with height difference
        return {
            "r": "beside",
            "a": pos_a,
            "b": pos_b,
            "props": {
                "distance_2d": d_2d,
                "height_diff": height_diff
            },
            "conf": max(0.7, confidence)
        }

    return None

def check_above_below(pos_a: Tuple[float,float,float], size_a: List[float],
                     pos_b: Tuple[float,float,float], size_b: List[float],
                     d_2d: float, height_diff: float) -> Optional[Dict[str,Any]]:
    """Check if one object is above/below another (but not on top)."""

    # Significant height difference required
    if height_diff < 0.5:  # At least 50cm height difference
        return None

    # Objects should be reasonably close in 2D
    if d_2d > 1.5:  # Within 1.5m in 2D plane
        return None

    relation_type = "above" if pos_a[2] > pos_b[2] else "below"
    confidence = min(0.8, 0.6 + (height_diff - 0.5) * 0.2)

    return {
        "r": relation_type,
        "a": pos_a,
        "b": pos_b,
        "props": {
            "height_diff": height_diff,
            "distance_2d": d_2d
        },
        "conf": confidence
    }

def relate_distance(node_a: Dict[str,Any], node_b: Dict[str,Any], d: float, near_thresh: float=0.8) -> Dict[str,Any]:
    """Distance-based relation detection (near/far)."""

    if d <= near_thresh:
        # For "near": Use a simple confidence that's always above acceptance threshold
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

# Backward compatibility
def relate_near(node_a: Dict[str,Any], node_b: Dict[str,Any], near_thresh: float=0.8) -> Dict[str,Any]:
    """Enhanced spatial relation detection (replaces simple near/far)."""
    relation = detect_spatial_relation(node_a, node_b)

    # Fix the node IDs (the detect_spatial_relation uses positions as placeholders)
    relation["a"] = node_a["id"]
    relation["b"] = node_b["id"]

    return relation

def visible_from(agent_pose, node: Dict[str,Any]) -> bool:
    # Placeholder: always true in PoC
    return True
