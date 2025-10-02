#!/usr/bin/env python3
"""
Simple Complex Apartment GUI Demo

A clean, focused GUI for the complex apartment scene with enhanced 3D visualization,
clear controls, and real-time spatial relationship monitoring.
"""

import json
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import threading
import time
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spacxt.core.graph_store import SceneGraph
from spacxt.core.orchestrator import Bus, make_agents, tick


class SimpleApartmentGUI:
    """Simple, focused GUI for the complex apartment scene."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SpacXT - Complex Apartment Demo")
        self.root.geometry("1200x800")

        # Scene data
        self.graph = None
        self.bus = None
        self.agents = None
        self.data = None
        self.running = False

        # Room colors for visualization
        self.room_colors = {
            "550e8400-e29b-41d4-a716-446655441001": "#E8F4FD",  # Living Room
            "550e8400-e29b-41d4-a716-446655441002": "#FFF2E8",  # Kitchen
            "550e8400-e29b-41d4-a716-446655441003": "#F0E8FF",  # Master Bedroom
            "550e8400-e29b-41d4-a716-446655441004": "#E8FFE8",  # Second Bedroom
            "550e8400-e29b-41d4-a716-446655441005": "#FFE8E8",  # Bathroom
            "550e8400-e29b-41d4-a716-446655441006": "#F8F8F8",  # Hallway
        }

        # Load the apartment scene
        self.load_apartment_scene()

        # Create GUI components
        self.create_gui()

        # Initial visualization
        self.update_visualization()

    def load_apartment_scene(self):
        """Load the complex apartment scene."""
        bootstrap_path = Path(__file__).parent / "complex_apartment.json"
        with open(bootstrap_path, "r") as f:
            self.data = json.load(f)

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

    def create_gui(self):
        """Create the main GUI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - 3D visualization
        left_frame = ttk.LabelFrame(main_frame, text="3D Apartment Visualization", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Right side - controls and info
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Scene info
        info_frame = ttk.LabelFrame(right_frame, text="Scene Information", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 5))

        self.info_text = tk.Text(info_frame, height=8, width=30, font=('Consolas', 9))
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Controls
        controls_frame = ttk.LabelFrame(right_frame, text="Controls", padding=5)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        # Control buttons
        self.start_btn = ttk.Button(controls_frame, text="Start Negotiation",
                                   command=self.toggle_negotiation)
        self.start_btn.pack(fill=tk.X, pady=2)

        self.step_btn = ttk.Button(controls_frame, text="Single Step",
                                  command=self.single_step)
        self.step_btn.pack(fill=tk.X, pady=2)

        self.reset_btn = ttk.Button(controls_frame, text="Reset Scene",
                                   command=self.reset_scene)
        self.reset_btn.pack(fill=tk.X, pady=2)

        self.export_btn = ttk.Button(controls_frame, text="Export Scene",
                                    command=self.export_scene)
        self.export_btn.pack(fill=tk.X, pady=2)

        # Relationship monitor
        rel_frame = ttk.LabelFrame(right_frame, text="Spatial Relationships", padding=5)
        rel_frame.pack(fill=tk.BOTH, expand=True)

        self.rel_text = scrolledtext.ScrolledText(rel_frame, height=15, width=30,
                                                 font=('Consolas', 8))
        self.rel_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - 29 objects loaded")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_visualization(self):
        """Update the 3D visualization."""
        self.ax.clear()

        # Draw room boundaries
        for room in self.data["scene"]["rooms"]:
            self.draw_room(room)

        # Draw objects
        for node_id, node in self.graph.nodes.items():
            self.draw_object(node)

        # Draw relationships
        self.draw_relationships()

        # Configure 3D view
        self.ax.set_xlim(-1, 11)
        self.ax.set_ylim(-1, 10)
        self.ax.set_zlim(0, 3.5)
        self.ax.set_xlabel('X (meters)')
        self.ax.set_ylabel('Y (meters)')
        self.ax.set_zlabel('Z (meters)')
        self.ax.set_title(f'{self.data["scene"]["name"]}\n{len(self.graph.nodes)} Objects ({len([n for n in self.graph.nodes.values() if n.cls != "wall"])} furniture, {len([n for n in self.graph.nodes.values() if n.cls == "wall"])} walls), {len(self.graph.relations)} Relationships')
        self.ax.view_init(elev=25, azim=45)

        # Update canvas
        self.canvas.draw()

        # Update info panels
        self.update_info_panel()
        self.update_relationship_panel()

    def draw_room(self, room):
        """Draw a room boundary."""
        bbox = room["bbox"]
        min_coords = bbox["min"]
        max_coords = bbox["max"]

        # Room floor rectangle
        vertices = [
            (min_coords[0], min_coords[1], 0.01),
            (max_coords[0], min_coords[1], 0.01),
            (max_coords[0], max_coords[1], 0.01),
            (min_coords[0], max_coords[1], 0.01)
        ]

        color = self.room_colors.get(room["id"], "#F0F0F0")
        collection = Poly3DCollection([vertices], facecolors=color, alpha=0.4, edgecolors='gray')
        self.ax.add_collection3d(collection)

        # Room label
        center_x = (min_coords[0] + max_coords[0]) / 2
        center_y = (min_coords[1] + max_coords[1]) / 2
        self.ax.text(center_x, center_y, 0.1, room["name"],
                    fontsize=10, ha='center', weight='bold', color='darkblue')

    def draw_object(self, node):
        """Draw a 3D object."""
        pos = node.pos
        bbox_size = node.bbox.get('xyz', [0.5, 0.5, 0.5])
        color = self.get_object_color(node.cls)

        # Draw 3D box
        self.draw_3d_box(pos, bbox_size, color, alpha=0.8)

        # Object label - use the same name resolution as in the relationship panel
        label = self.get_object_name(node.id)
        self.ax.text(pos[0], pos[1], pos[2] + bbox_size[2]/2 + 0.1,
                    label, fontsize=6, ha='center', color='black')

    def draw_3d_box(self, center, size, color, alpha=0.8):
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
        self.ax.add_collection3d(collection)

    def draw_relationships(self):
        """Draw spatial relationships as lines."""
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a not in self.graph.nodes or b not in self.graph.nodes or rel_type == 'in':
                continue

            node_a = self.graph.nodes[a]
            node_b = self.graph.nodes[b]

            # Line style based on relationship type
            if rel_type == 'beside':
                color, style, width = 'green', '-', 2
            elif rel_type == 'on_top_of':
                color, style, width = 'red', '-', 3
            elif rel_type in ['above', 'below']:
                color, style, width = 'blue', '--', 1
            else:
                color, style, width = 'gray', ':', 1

            self.ax.plot([node_a.pos[0], node_b.pos[0]],
                        [node_a.pos[1], node_b.pos[1]],
                        [node_a.pos[2], node_b.pos[2]],
                        color=color, linestyle=style, linewidth=width, alpha=0.7)

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

    def update_info_panel(self):
        """Update the scene information panel."""
        self.info_text.delete(1.0, tk.END)

        info = f"SCENE: {self.data['scene']['name']}\n\n"
        info += f"Objects: {len(self.graph.nodes)}\n"
        info += f"Relationships: {len(self.graph.relations)}\n"
        info += f"Rooms: {len(self.data['scene']['rooms'])}\n"
        info += f"Agents: {len(self.agents)}\n\n"

        # Object breakdown
        obj_types = {}
        for node in self.graph.nodes.values():
            obj_types[node.cls] = obj_types.get(node.cls, 0) + 1

        info += "OBJECT TYPES:\n"
        for obj_type, count in sorted(obj_types.items()):
            info += f"  {obj_type}: {count}\n"

        self.info_text.insert(1.0, info)

    def update_relationship_panel(self):
        """Update the relationships panel."""
        self.rel_text.delete(1.0, tk.END)

        # Group relationships by type
        rel_by_type = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append((a, b, relation.conf))

        # Display each type
        for rel_type, relationships in sorted(rel_by_type.items()):
            self.rel_text.insert(tk.END, f"{rel_type.upper()} ({len(relationships)}):\n")

            # Show top relationships by confidence
            for a, b, conf in sorted(relationships, key=lambda x: -x[2])[:5]:
                a_name = self.get_object_name(a)
                b_name = self.get_object_name(b)
                self.rel_text.insert(tk.END, f"  {a_name} → {b_name} ({conf:.2f})\n")

            if len(relationships) > 5:
                self.rel_text.insert(tk.END, f"  ... and {len(relationships)-5} more\n")

            self.rel_text.insert(tk.END, "\n")

    def get_object_name(self, obj_id):
        """Get object name from UUID."""
        # Check if it's a room
        if obj_id.startswith("550e8400-e29b-41d4-a716-446655441"):
            room_names = {room["id"]: room["name"] for room in self.data["scene"]["rooms"]}
            return room_names.get(obj_id, f"Room-{obj_id[-4:]}")

        # Check if it's an object
        node = self.graph.nodes.get(obj_id)
        if node:
            # Always prioritize the name field if it exists and is not empty
            if hasattr(node, 'name') and node.name:
                return node.name
            # Fallback to generating name from class
            return self.get_name_from_class(node.cls)

        return obj_id[-8:]  # Last 8 chars of UUID as final fallback

    def get_name_from_class(self, cls):
        """Generate a readable name from object class."""
        name_mapping = {
            "sofa": "Sofa", "table": "Table", "tv_stand": "TV Stand",
            "tv": "Television", "counter": "Counter", "refrigerator": "Refrigerator",
            "stove": "Stove", "chair": "Chair", "bed": "Bed",
            "nightstand": "Nightstand", "wardrobe": "Wardrobe", "desk": "Desk",
            "toilet": "Toilet", "sink": "Sink", "shower": "Shower",
            "wall": "Wall", "door": "Door"
        }
        return name_mapping.get(cls, cls.title())

    def toggle_negotiation(self):
        """Start/stop continuous negotiation."""
        if not self.running:
            self.running = True
            self.start_btn.config(text="Stop Negotiation")
            self.status_var.set("Running spatial negotiation...")

            # Start negotiation thread
            self.negotiation_thread = threading.Thread(target=self.run_negotiation, daemon=True)
            self.negotiation_thread.start()
        else:
            self.running = False
            self.start_btn.config(text="Start Negotiation")
            self.status_var.set("Negotiation stopped")

    def run_negotiation(self):
        """Run continuous negotiation."""
        while self.running:
            initial_count = len(self.graph.relations)
            tick(self.graph, self.bus, self.agents)
            new_count = len(self.graph.relations)

            if new_count != initial_count:
                # Update visualization on main thread
                self.root.after(0, self.update_visualization)
                self.root.after(0, lambda: self.status_var.set(
                    f"New relationships discovered! Total: {new_count}"))

            time.sleep(0.5)

    def single_step(self):
        """Run a single negotiation step."""
        initial_count = len(self.graph.relations)
        tick(self.graph, self.bus, self.agents)
        new_count = len(self.graph.relations)

        self.update_visualization()
        self.status_var.set(f"Step complete: {initial_count} → {new_count} relationships")

    def reset_scene(self):
        """Reset the scene to initial state."""
        self.running = False
        self.start_btn.config(text="Start Negotiation")

        # Reload scene
        self.load_apartment_scene()
        self.update_visualization()
        self.status_var.set("Scene reset to initial state")

    def export_scene(self):
        """Export the current scene."""
        try:
            from complex_apartment_demo import SceneExporter

            exporter = SceneExporter(self.graph)
            export_path = Path(__file__).parent / "apartment_gui_simple_export.json"

            exported_data = exporter.export_scene_with_relationships(str(export_path))

            messagebox.showinfo("Export Complete",
                              f"Scene exported successfully!\n\n"
                              f"File: {export_path.name}\n"
                              f"Objects: {exported_data['scene']['export_metadata']['total_objects']}\n"
                              f"Relationships: {exported_data['scene']['export_metadata']['total_relationships']}")

            self.status_var.set(f"Scene exported to {export_path.name}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export scene:\n{str(e)}")
            self.status_var.set("Export failed")

    def run(self):
        """Start the GUI."""
        print("🏠 Complex Apartment GUI Started")
        print("   Use the controls on the right to interact with the scene")
        print("   The 3D view shows the apartment layout with spatial relationships")
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = SimpleApartmentGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
