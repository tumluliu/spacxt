#!/usr/bin/env python3
"""
Complex Apartment Matplotlib Demo - Interactive visualization using matplotlib only.

This demo creates an interactive apartment visualization using only matplotlib,
avoiding tkinter dependency issues. It shows the apartment layout, runs spatial
negotiation, and provides interactive controls.
"""

import json
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.widgets as widgets
from pathlib import Path
import numpy as np
import threading
import time

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spacxt.core.graph_store import SceneGraph
from spacxt.core.orchestrator import Bus, make_agents, tick


class ApartmentMatplotlibDemo:
    """Interactive apartment demo using matplotlib only."""

    def __init__(self):
        self.graph = None
        self.bus = None
        self.agents = None
        self.data = None
        self.running = False

        # Room colors
        self.room_colors = {
            "550e8400-e29b-41d4-a716-446655441001": "#E8F4FD",  # Living Room
            "550e8400-e29b-41d4-a716-446655441002": "#FFF2E8",  # Kitchen
            "550e8400-e29b-41d4-a716-446655441003": "#F0E8FF",  # Master Bedroom
            "550e8400-e29b-41d4-a716-446655441004": "#E8FFE8",  # Second Bedroom
            "550e8400-e29b-41d4-a716-446655441005": "#FFE8E8",  # Bathroom
            "550e8400-e29b-41d4-a716-446655441006": "#F8F8F8",  # Hallway
        }

        self.room_names = {}

        # Load scene
        self.load_scene()

        # Create figure and subplots
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle('Complex Apartment - SpacXT Spatial Reasoning Demo', fontsize=16, fontweight='bold')

        # 3D view (main visualization)
        self.ax_3d = self.fig.add_subplot(221, projection='3d')

        # 2D floor plan
        self.ax_2d = self.fig.add_subplot(222)

        # Relationship graph
        self.ax_graph = self.fig.add_subplot(223)

        # Statistics/info panel
        self.ax_info = self.fig.add_subplot(224)
        self.ax_info.axis('off')

        # Create control buttons
        self.create_controls()

        # Initial drawing
        self.update_all_views()

    def load_scene(self):
        """Load the apartment scene."""
        bootstrap_path = Path(__file__).parent / "complex_apartment.json"
        with open(bootstrap_path, "r") as f:
            self.data = json.load(f)

        # Build room name mapping
        self.room_names = {
            room["id"]: room["name"] for room in self.data["scene"]["rooms"]
        }

        # Initialize scene graph
        self.graph = SceneGraph()
        self.graph.load_bootstrap(self.data)

        # Create agents
        self.bus = Bus()
        agent_ids = [obj["id"] for obj in self.data["scene"]["objects"]]
        self.agents = make_agents(self.graph, self.bus, agent_ids)

        print(f"✅ Loaded: {self.data['scene']['name']}")
        print(f"   Objects: {len(self.graph.nodes)}")
        print(f"   Rooms: {len(self.data['scene']['rooms'])}")
        print(f"   Agents: {len(self.agents)}")

    def create_controls(self):
        """Create interactive control buttons."""
        # Button positions (left, bottom, width, height)
        btn_height = 0.04
        btn_width = 0.1
        btn_spacing = 0.02

        # Start/Stop button
        self.ax_start = plt.axes([0.02, 0.02, btn_width, btn_height])
        self.btn_start = widgets.Button(self.ax_start, 'Start Negotiation')
        self.btn_start.on_clicked(self.toggle_negotiation)

        # Step button
        self.ax_step = plt.axes([0.02 + btn_width + btn_spacing, 0.02, btn_width, btn_height])
        self.btn_step = widgets.Button(self.ax_step, 'Single Step')
        self.btn_step.on_clicked(self.single_step)

        # Reset button
        self.ax_reset = plt.axes([0.02 + 2*(btn_width + btn_spacing), 0.02, btn_width, btn_height])
        self.btn_reset = widgets.Button(self.ax_reset, 'Reset Scene')
        self.btn_reset.on_clicked(self.reset_scene)

        # Export button
        self.ax_export = plt.axes([0.02 + 3*(btn_width + btn_spacing), 0.02, btn_width, btn_height])
        self.btn_export = widgets.Button(self.ax_export, 'Export Scene')
        self.btn_export.on_clicked(self.export_scene)

    def update_all_views(self):
        """Update all visualization views."""
        self.draw_3d_view()
        self.draw_2d_floor_plan()
        self.draw_relationship_graph()
        self.update_info_panel()
        self.fig.canvas.draw()

    def draw_3d_view(self):
        """Draw the main 3D apartment view."""
        self.ax_3d.clear()

        # Draw room boundaries
        for room in self.data["scene"]["rooms"]:
            bbox = room["bbox"]
            min_coords = bbox["min"]
            max_coords = bbox["max"]

            # Room floor
            vertices = [
                (min_coords[0], min_coords[1], 0.01),
                (max_coords[0], min_coords[1], 0.01),
                (max_coords[0], max_coords[1], 0.01),
                (min_coords[0], max_coords[1], 0.01)
            ]

            color = self.room_colors.get(room["id"], "#F0F0F0")
            collection = Poly3DCollection([vertices], facecolors=color, alpha=0.3, edgecolors='gray')
            self.ax_3d.add_collection3d(collection)

            # Room label
            center_x = (min_coords[0] + max_coords[0]) / 2
            center_y = (min_coords[1] + max_coords[1]) / 2
            self.ax_3d.text(center_x, center_y, 0.1, room["name"],
                           fontsize=8, ha='center', weight='bold', color='darkblue')

        # Draw objects
        for node_id, node in self.graph.nodes.items():
            pos = node.pos
            bbox_size = node.bbox.get('xyz', [0.5, 0.5, 0.5])
            color = self.get_object_color(node.cls)

            self.draw_3d_box(pos, bbox_size, color, alpha=0.7)

            # Object label
            label = getattr(node, 'name', node.cls.title()) if hasattr(node, 'name') and node.name else node.cls.title()
            self.ax_3d.text(pos[0], pos[1], pos[2] + bbox_size[2]/2 + 0.1,
                           label, fontsize=5, ha='center', color='black')

        # Draw relationships (non-room)
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a not in self.graph.nodes or b not in self.graph.nodes or rel_type == 'in':
                continue

            node_a = self.graph.nodes[a]
            node_b = self.graph.nodes[b]

            if rel_type == 'beside':
                color, style, width = 'green', '-', 2
            elif rel_type == 'on_top_of':
                color, style, width = 'red', '-', 3
            elif rel_type in ['above', 'below']:
                color, style, width = 'blue', '--', 1
            else:
                color, style, width = 'gray', ':', 1

            self.ax_3d.plot([node_a.pos[0], node_b.pos[0]],
                           [node_a.pos[1], node_b.pos[1]],
                           [node_a.pos[2], node_b.pos[2]],
                           color=color, linestyle=style, linewidth=width, alpha=0.6)

        # Set up 3D view
        self.ax_3d.set_xlim(-1, 11)
        self.ax_3d.set_ylim(-1, 10)
        self.ax_3d.set_zlim(0, 3.5)
        self.ax_3d.set_xlabel('X (m)')
        self.ax_3d.set_ylabel('Y (m)')
        self.ax_3d.set_zlabel('Z (m)')
        self.ax_3d.set_title('3D Apartment View')
        self.ax_3d.view_init(elev=20, azim=45)

    def draw_2d_floor_plan(self):
        """Draw 2D floor plan view."""
        self.ax_2d.clear()

        # Draw room boundaries
        for room in self.data["scene"]["rooms"]:
            bbox = room["bbox"]
            min_coords = bbox["min"]
            max_coords = bbox["max"]

            # Room rectangle
            from matplotlib.patches import Rectangle
            rect = Rectangle((min_coords[0], min_coords[1]),
                           max_coords[0] - min_coords[0],
                           max_coords[1] - min_coords[1],
                           facecolor=self.room_colors.get(room["id"], "#F0F0F0"),
                           edgecolor='gray', alpha=0.5)
            self.ax_2d.add_patch(rect)

            # Room label
            center_x = (min_coords[0] + max_coords[0]) / 2
            center_y = (min_coords[1] + max_coords[1]) / 2
            self.ax_2d.text(center_x, center_y, room["name"],
                           fontsize=8, ha='center', weight='bold', color='darkblue')

        # Draw objects (top-down view)
        for node_id, node in self.graph.nodes.items():
            pos = node.pos
            bbox_size = node.bbox.get('xyz', [0.5, 0.5, 0.5])
            color = self.get_object_color(node.cls)

            # Object rectangle
            rect = Rectangle((pos[0] - bbox_size[0]/2, pos[1] - bbox_size[1]/2),
                           bbox_size[0], bbox_size[1],
                           facecolor=color, edgecolor='black', alpha=0.7)
            self.ax_2d.add_patch(rect)

        self.ax_2d.set_xlim(-1, 11)
        self.ax_2d.set_ylim(-1, 10)
        self.ax_2d.set_xlabel('X (m)')
        self.ax_2d.set_ylabel('Y (m)')
        self.ax_2d.set_title('Floor Plan View')
        self.ax_2d.set_aspect('equal')

    def draw_relationship_graph(self):
        """Draw relationship network graph."""
        self.ax_graph.clear()

        # Count relationships by type
        rel_counts = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        if rel_counts:
            # Create bar chart
            rel_types = list(rel_counts.keys())
            counts = list(rel_counts.values())

            bars = self.ax_graph.bar(rel_types, counts, color=['skyblue', 'lightgreen', 'salmon', 'gold', 'plum'][:len(rel_types)])

            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.ax_graph.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                  str(count), ha='center', va='bottom', fontsize=8)

        self.ax_graph.set_title('Spatial Relationships')
        self.ax_graph.set_ylabel('Count')
        plt.setp(self.ax_graph.get_xticklabels(), rotation=45, ha='right')

    def update_info_panel(self):
        """Update the information panel."""
        self.ax_info.clear()
        self.ax_info.axis('off')

        # Scene statistics
        info_text = f"SCENE: {self.data['scene']['name']}\n\n"
        info_text += f"📊 STATISTICS\n"
        info_text += f"Objects: {len(self.graph.nodes)}\n"
        info_text += f"Relationships: {len(self.graph.relations)}\n"
        info_text += f"Rooms: {len(self.data['scene']['rooms'])}\n"
        info_text += f"Agents: {len(self.agents)}\n\n"

        # Relationship breakdown
        rel_counts = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        info_text += "🔗 RELATIONSHIPS\n"
        for rel_type, count in sorted(rel_counts.items()):
            info_text += f"{rel_type}: {count}\n"

        # Status
        status = "🔄 Running" if self.running else "⏸️ Stopped"
        info_text += f"\nStatus: {status}"

        self.ax_info.text(0.05, 0.95, info_text, transform=self.ax_info.transAxes,
                         fontsize=9, verticalalignment='top', fontfamily='monospace')

    def get_object_color(self, obj_class):
        """Get color for object based on its class."""
        color_map = {
            'sofa': '#8B4513', 'table': '#DEB887', 'tv_stand': '#696969',
            'tv': '#000000', 'counter': '#D2691E', 'refrigerator': '#FFFFFF',
            'stove': '#C0C0C0', 'chair': '#CD853F', 'bed': '#4682B4',
            'nightstand': '#8B7355', 'wardrobe': '#8B4513', 'desk': '#DEB887',
            'toilet': '#FFFFFF', 'sink': '#E6E6FA', 'shower': '#E0E0E0',
            'wall': '#A0A0A0', 'door': '#8B4513',
        }
        return color_map.get(obj_class, '#808080')

    def draw_3d_box(self, center, size, color, alpha=0.7):
        """Draw a 3D box."""
        x, y, z = center
        dx, dy, dz = size

        vertices = [
            [x-dx/2, y-dy/2, z-dz/2], [x+dx/2, y-dy/2, z-dz/2],
            [x+dx/2, y+dy/2, z-dz/2], [x-dx/2, y+dy/2, z-dz/2],
            [x-dx/2, y-dy/2, z+dz/2], [x+dx/2, y-dy/2, z+dz/2],
            [x+dx/2, y+dy/2, z+dz/2], [x-dx/2, y+dy/2, z+dz/2]
        ]

        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[2], vertices[3], vertices[7], vertices[6]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]]
        ]

        collection = Poly3DCollection(faces, facecolors=color, alpha=alpha,
                                    edgecolors='black', linewidth=0.5)
        self.ax_3d.add_collection3d(collection)

    def toggle_negotiation(self, event):
        """Start/stop continuous negotiation."""
        if not self.running:
            self.running = True
            self.btn_start.label.set_text('Stop Negotiation')
            # Start negotiation in a separate thread
            self.negotiation_thread = threading.Thread(target=self.run_negotiation, daemon=True)
            self.negotiation_thread.start()
        else:
            self.running = False
            self.btn_start.label.set_text('Start Negotiation')

    def run_negotiation(self):
        """Run continuous negotiation in background."""
        while self.running:
            initial_count = len(self.graph.relations)
            tick(self.graph, self.bus, self.agents)
            new_count = len(self.graph.relations)

            if new_count != initial_count:
                # Update visualization on main thread
                self.fig.canvas.draw_idle()

            time.sleep(0.5)  # Negotiation interval

    def single_step(self, event):
        """Run a single negotiation step."""
        initial_count = len(self.graph.relations)
        tick(self.graph, self.bus, self.agents)
        new_count = len(self.graph.relations)

        print(f"Step: {initial_count} → {new_count} relationships")
        self.update_all_views()

    def reset_scene(self, event):
        """Reset the scene to initial state."""
        self.running = False
        self.btn_start.label.set_text('Start Negotiation')

        # Reload the scene
        self.load_scene()
        self.update_all_views()
        print("Scene reset to initial state")

    def export_scene(self, event):
        """Export the current scene."""
        try:
            from complex_apartment_demo import SceneExporter

            exporter = SceneExporter(self.graph)
            export_path = Path(__file__).parent / "apartment_matplotlib_export.json"

            exported_data = exporter.export_scene_with_relationships(str(export_path))
            print(f"✅ Scene exported to: {export_path}")
            print(f"   Objects: {exported_data['scene']['export_metadata']['total_objects']}")
            print(f"   Relationships: {exported_data['scene']['export_metadata']['total_relationships']}")

        except Exception as e:
            print(f"❌ Export error: {e}")

    def run(self):
        """Start the interactive demo."""
        print("\n🎯 Interactive Controls:")
        print("   • Start Negotiation: Begin continuous spatial reasoning")
        print("   • Single Step: Run one negotiation round")
        print("   • Reset Scene: Return to initial state")
        print("   • Export Scene: Save current state with relationships")
        print("\n📊 Views:")
        print("   • Top Left: 3D apartment visualization")
        print("   • Top Right: 2D floor plan")
        print("   • Bottom Left: Relationship statistics")
        print("   • Bottom Right: Scene information")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    print("🏠 Starting Complex Apartment Matplotlib Demo...")
    try:
        demo = ApartmentMatplotlibDemo()
        demo.run()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
