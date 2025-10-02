#!/usr/bin/env python3
"""
3DSG Parser - Convert System A scene data to unified scene graph format.

This script converts scene data from System A (which uses NED coordinate system)
to the standard coordinate system expected by the spatial context system.

NED (North-East-Down) to Standard conversion:
- NED: X=North, Y=East, Z=Down
- Standard: X=Right, Y=Up, Z=Forward
- Conversion: [x, y, z] -> [y, -z, x]
"""
import os
import json
import uuid
import math


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def normalize(v):
    norm = math.sqrt(sum(x*x for x in v))
    return [x / norm for x in v] if norm > 1e-8 else [0, 0, 0]


def convert_ned_to_standard(pos):
    """Convert NED (North-East-Down) coordinates to standard 3D coordinates.
    NED: X=North, Y=East, Z=Down
    Standard: X=Right, Y=Up, Z=Forward (or similar right-handed system)
    """
    if len(pos) != 3:
        return pos
    x, y, z = pos
    # Convert NED to standard: flip Z (down becomes up), swap X and Y
    return [y, -z, x]


def convert_ned_orientation_to_standard(ori):
    """Convert NED orientation to standard coordinate system.
    This affects the normal vectors and quaternions.
    """
    if len(ori) != 3:
        return ori
    x, y, z = ori
    # Apply same transformation as position
    return [y, -z, x]


def parse_bbox_to_minmax(bbox):
    """System A room bbox format: [xmin, ymin, zmin, xmax, ymax, zmax]."""
    if not bbox or len(bbox) < 6:
        return {"min": [0, 0, 0], "max": [0, 0, 0]}

    # Convert NED coordinates to standard coordinate system
    min_pos = convert_ned_to_standard([bbox[0], bbox[1], bbox[2]])
    max_pos = convert_ned_to_standard([bbox[3], bbox[4], bbox[5]])

    return {
        "min": min_pos,
        "max": max_pos,
    }


def parse_object_bbox(bbox):
    """System A object bbox = 24 coords (8 vertices). We approximate with extents."""
    if not bbox or len(bbox) % 3 != 0:
        return {"type": "OBB", "xyz": [0, 0, 0]}

    # Convert all 8 vertices from NED to standard coordinate system
    converted_vertices = []
    for i in range(0, len(bbox), 3):
        if i + 2 < len(bbox):
            vertex = convert_ned_to_standard([bbox[i], bbox[i+1], bbox[i+2]])
            converted_vertices.extend(vertex)

    # Calculate extents from converted vertices
    if len(converted_vertices) >= 9:  # At least 3 vertices
        xs = converted_vertices[0::3]
        ys = converted_vertices[1::3]
        zs = converted_vertices[2::3]
        extent = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]
    else:
        extent = [0, 0, 0]

    return {"type": "OBB", "xyz": extent}


def compute_centroid(bbox):
    if bbox and len(bbox) % 3 == 0:
        # First compute centroid in NED coordinates
        xs = bbox[0::3]
        ys = bbox[1::3]
        zs = bbox[2::3]
        ned_centroid = [sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs)]

        # Convert to standard coordinate system
        return convert_ned_to_standard(ned_centroid)
    return [0, 0, 0]


def convert_scene(system_a_dir, scene_name="Converted Scene", frame="map"):
    rooms_dir = os.path.join(system_a_dir, "rooms")
    objects_dir = os.path.join(system_a_dir, "objects")

    rooms = []
    objects = []
    relations = []

    room_id_map = {}
    object_id_map = {}

    # --- Rooms ---
    if os.path.isdir(rooms_dir):
        for fname in os.listdir(rooms_dir):
            if not fname.endswith(".json"):
                continue
            room_data = load_json(os.path.join(rooms_dir, fname))
            rid = generate_uuid()
            room_id_map[room_data["room_id"]] = rid
            rooms.append({
                "id": rid,
                "name": room_data.get("name", "room"),
                "bbox": parse_bbox_to_minmax(room_data.get("bbox", []))
            })

    # --- Objects ---
    if os.path.isdir(objects_dir):
        for fname in os.listdir(objects_dir):
            if not fname.endswith(".json"):
                continue
            obj_data = load_json(os.path.join(objects_dir, fname))
            oid = generate_uuid()
            object_id_map[obj_data["object_id"]] = oid

            bbox = obj_data.get("bbox", [])
            pos = compute_centroid(bbox)

            # Orientation from normal_vector (convert from NED to standard)
            normal = obj_data.get("normal_vector")
            if isinstance(normal, list) and len(normal) == 3:
                # Convert normal vector from NED to standard coordinate system
                converted_normal = convert_ned_orientation_to_standard(normal)
                nx, ny, nz = normalize(converted_normal)
                ori = [nx, ny, nz, 0.0]
            else:
                ori = [0, 0, 0, 1]

            objects.append({
                "id": oid,
                "name": obj_data.get("name", "object"),
                "cls": obj_data.get("name", "object").lower().replace(" ", "_"),
                "pos": pos,
                "ori": ori,
                "bbox": parse_object_bbox(bbox),
                "aff": [],
                "lom": "medium",
                "conf": 1.0,
            })

            # Add relation: object in room
            rid = obj_data.get("room_id")
            if rid in room_id_map:
                relations.append({
                    "r": "in",
                    "a": oid,
                    "b": room_id_map[rid]
                })

    scene = {
        "scene": {
            "id": generate_uuid(),
            "name": scene_name,
            "frame": frame,
            "rooms": rooms,
            "objects": objects,
            "relations": relations,
        }
    }
    return scene


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert System A scene dir into unified scene graph JSON.")
    parser.add_argument("input_dir", help="System A scene directory (with setup.json, rooms/, objects/)")
    parser.add_argument("-o", "--output", default="scene_graph.json", help="Output JSON file")
    parser.add_argument("--name", default="Converted Scene", help="Scene name")
    args = parser.parse_args()

    scene_json = convert_scene(args.input_dir, scene_name=args.name)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(scene_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote scene graph JSON to {args.output}")
