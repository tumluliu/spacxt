#!/usr/bin/env python3
"""
Complex Apartment Demo with Scene Export Functionality

This demo creates a realistic 80 sqm apartment with multiple rooms, walls, doors,
and furniture. It runs spatial relationship negotiation and exports the final
scene graph with all discovered relationships and confidence values.
"""

import json
import uuid
import time
from pathlib import Path
from typing import Dict, Any

# Import SpacXT components
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from spacxt.core.graph_store import SceneGraph
from spacxt.core.orchestrator import Bus, make_agents, tick


class SceneExporter:
    """Exports scene graphs with full relationship data including confidence values."""

    def __init__(self, scene_graph: SceneGraph):
        self.graph = scene_graph

    def export_scene_with_relationships(self, output_path: str = None) -> Dict[str, Any]:
        """
        Export the complete scene graph including all discovered relationships
        with confidence values.

        Args:
            output_path: Optional file path to save the exported scene

        Returns:
            Dictionary containing the complete scene data
        """

        # Build the scene structure - preserve original room data from bootstrap
        with open(Path(__file__).parent / "complex_apartment.json", 'r') as f:
            bootstrap_data = json.load(f)

        scene_data = {
            "scene": {
                "id": bootstrap_data["scene"]["id"],
                "name": bootstrap_data["scene"]["name"],
                "frame": "map",
                "export_timestamp": time.time(),
                "export_metadata": {
                    "total_objects": len(self.graph.nodes),
                    "total_relationships": len(self.graph.relations),
                    "negotiation_events": len(self.graph.events)
                },
                "rooms": bootstrap_data["scene"]["rooms"],  # Preserve original room UUIDs and names
                "objects": [],
                "relations": []
            }
        }

        # Export all objects with their current state
        for obj_id, node in self.graph.nodes.items():
            obj_data = {
                "id": obj_id,
                "name": getattr(node, 'name', self._generate_name_from_class(node.cls)),
                "cls": node.cls,
                "pos": list(node.pos),
                "ori": list(node.ori),
                "bbox": node.bbox,
                "aff": node.aff,
                "lom": node.lom,
                "conf": node.conf
            }

            # Include state if present
            if hasattr(node, 'state') and node.state:
                obj_data["state"] = node.state

            # Include meta if present
            if hasattr(node, 'meta') and node.meta:
                obj_data["meta"] = node.meta

            scene_data["scene"]["objects"].append(obj_data)

        # Export all relationships with full confidence data
        for (rel_type, a, b), relation in self.graph.relations.items():
            rel_data = {
                "r": rel_type,
                "a": a,
                "b": b,
                "conf": relation.conf,
                "timestamp": relation.ts if hasattr(relation, 'ts') else None
            }

            # Include relationship properties if present
            if hasattr(relation, 'props') and relation.props:
                rel_data["props"] = relation.props

            scene_data["scene"]["relations"].append(rel_data)

        # Include negotiation history
        scene_data["scene"]["negotiation_history"] = self.graph.events[-10:]  # Last 10 events

        # Save to file if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(scene_data, f, indent=2, default=str)
            print(f"Scene exported to: {output_path}")

        return scene_data

    def _generate_name_from_class(self, cls: str) -> str:
        """Generate a readable name from object class."""
        name_mapping = {
            "sofa": "Sofa",
            "table": "Table",
            "tv_stand": "TV Stand",
            "tv": "Television",
            "counter": "Counter",
            "refrigerator": "Refrigerator",
            "stove": "Stove",
            "chair": "Chair",
            "bed": "Bed",
            "nightstand": "Nightstand",
            "wardrobe": "Wardrobe",
            "desk": "Desk",
            "toilet": "Toilet",
            "sink": "Sink",
            "shower": "Shower",
            "wall": "Wall",
            "door": "Door"
        }
        return name_mapping.get(cls, cls.title())

    def print_relationship_summary(self):
        """Print a summary of discovered relationships."""

        print("\n" + "="*60)
        print("SPATIAL RELATIONSHIP SUMMARY")
        print("="*60)

        # Group relationships by type
        rel_by_type = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append((a, b, relation.conf))

        # Print each relationship type
        for rel_type, relationships in sorted(rel_by_type.items()):
            print(f"\n{rel_type.upper()} relationships ({len(relationships)}):")
            for a, b, conf in sorted(relationships, key=lambda x: -x[2]):  # Sort by confidence
                a_name = self._get_object_name(a)
                b_name = self._get_object_name(b)
                print(f"  {a_name} → {b_name} (confidence: {conf:.2f})")

    def _get_object_name(self, obj_id: str) -> str:
        """Get object name or generate from class."""
        # Check if it's a room UUID
        if obj_id.startswith("550e8400-e29b-41d4-a716-446655441"):
            room_names = {
                "550e8400-e29b-41d4-a716-446655441001": "Living Room",
                "550e8400-e29b-41d4-a716-446655441002": "Kitchen",
                "550e8400-e29b-41d4-a716-446655441003": "Master Bedroom",
                "550e8400-e29b-41d4-a716-446655441004": "Second Bedroom",
                "550e8400-e29b-41d4-a716-446655441005": "Bathroom",
                "550e8400-e29b-41d4-a716-446655441006": "Hallway"
            }
            return room_names.get(obj_id, f"Room-{obj_id[-4:]}")

        # Check if it's an object
        node = self.graph.nodes.get(obj_id)
        if node:
            if hasattr(node, 'name') and node.name:
                return node.name
            return self._generate_name_from_class(node.cls)
        return obj_id


def load_complex_apartment() -> SceneGraph:
    """Load the complex apartment scene from JSON."""

    # Load the bootstrap data
    bootstrap_path = Path(__file__).parent / "complex_apartment.json"

    with open(bootstrap_path, 'r') as f:
        bootstrap_data = json.load(f)

    # Create and initialize scene graph
    graph = SceneGraph(auto_physics=True)
    graph.load_bootstrap(bootstrap_data)

    return graph


def run_complex_apartment_demo():
    """Run the complete apartment demo with relationship negotiation and export."""

    print("🏠 SpacXT Complex Apartment Demo")
    print("="*50)

    # Load the apartment scene
    print("📦 Loading complex apartment scene...")
    graph = load_complex_apartment()

    # Count rooms from the bootstrap data
    with open(Path(__file__).parent / "complex_apartment.json", 'r') as f:
        bootstrap_data = json.load(f)
    num_rooms = len(bootstrap_data["scene"]["rooms"])

    print(f"✅ Loaded {len(graph.nodes)} objects in {num_rooms} rooms")
    print(f"   Scene: {bootstrap_data['scene']['name']} (UUID: {bootstrap_data['scene']['id']})")
    print(f"   All entities use UUIDs for unique identification")

    # Initialize communication bus and agents
    print("🤖 Creating autonomous agents...")
    bus = Bus()

    # Get all object IDs for agent creation
    object_ids = list(graph.nodes.keys())
    agents = make_agents(graph, bus, object_ids)

    print(f"✅ Created {len(agents)} autonomous agents")

    # Run initial relationship discovery
    print("\n🧠 Starting spatial relationship negotiation...")
    print("   (This may take a moment for a complex scene)")

    initial_relations = len(graph.relations)

    # Run multiple negotiation rounds
    for round_num in range(15):  # More rounds for complex scene
        tick(graph, bus, agents)

        current_relations = len(graph.relations)
        if round_num % 3 == 0:  # Progress update every 3 rounds
            new_relations = current_relations - initial_relations
            print(f"   Round {round_num + 1}: {new_relations} new relationships discovered")

    final_relations = len(graph.relations)
    discovered_relations = final_relations - initial_relations

    print(f"\n🎉 Negotiation complete!")
    print(f"   Initial relationships: {initial_relations}")
    print(f"   Final relationships: {final_relations}")
    print(f"   Newly discovered: {discovered_relations}")

    # Create exporter and show summary
    exporter = SceneExporter(graph)
    exporter.print_relationship_summary()

    # Export the scene
    export_path = Path(__file__).parent / "complex_apartment_negotiated.json"
    print(f"\n💾 Exporting scene with relationships...")

    exported_data = exporter.export_scene_with_relationships(str(export_path))

    print(f"✅ Scene exported to: {export_path}")
    print(f"   Total objects: {exported_data['scene']['export_metadata']['total_objects']}")
    print(f"   Total relationships: {exported_data['scene']['export_metadata']['total_relationships']}")

    # Show some interesting discovered relationships
    print("\n🔍 Sample discovered relationships:")
    interesting_rels = ["near", "supports", "on_top_of", "adjacent_to", "faces"]

    for rel_type in interesting_rels:
        matching_rels = [(a, b, rel.conf) for (r, a, b), rel in graph.relations.items() if r == rel_type]
        if matching_rels:
            print(f"\n   {rel_type.upper()}:")
            # Show top 3 by confidence
            for a, b, conf in sorted(matching_rels, key=lambda x: -x[2])[:3]:
                a_name = exporter._get_object_name(a)
                b_name = exporter._get_object_name(b)
                print(f"     {a_name} → {b_name} (conf: {conf:.2f})")

    return graph, exported_data


if __name__ == "__main__":
    try:
        graph, exported_data = run_complex_apartment_demo()

        print("\n" + "="*50)
        print("✨ Demo completed successfully!")
        print("   Check 'complex_apartment_negotiated.json' for full results")
        print("="*50)

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
