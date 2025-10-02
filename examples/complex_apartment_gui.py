#!/usr/bin/env python3
"""
Complex Apartment GUI Demo - Interactive 3D visualization of the realistic apartment scene.

This demo shows the complex apartment with multiple rooms, walls, doors, and furniture
in an interactive 3D GUI with enhanced visualization for the larger, more realistic scene.

Features:
- 3D visualization optimized for the complex apartment layout
- Room-based color coding for better organization
- Enhanced object labeling with names and UUIDs
- Real-time agent activity monitoring for 29 objects
- Interactive controls with apartment-specific features
- Export functionality for negotiated relationships

Usage:
    python complex_apartment_gui.py
"""

import json
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import threading
import time
from typing import Dict, Any
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Add the src directory to the path so we can import spacxt
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from spacxt.core.graph_store import SceneGraph
    from spacxt.core.orchestrator import Bus, make_agents, tick
    from spacxt.gui.visualizer import SceneVisualizer
except ImportError as e:
    print("❌ Error importing SpacXT components:")
    print(f"   {e}")
    print("\n💡 Make sure you have the required dependencies installed:")
    print("   pip install matplotlib numpy")
    sys.exit(1)


class ComplexApartmentVisualizer(SceneVisualizer):
    """Enhanced visualizer specifically for the complex apartment scene."""

    def __init__(self, scene_graph: SceneGraph, bus: Bus, agents: Dict[str, Any]):
        # Load bootstrap data for room information
        self.bootstrap_path = Path(__file__).parent / "complex_apartment.json"
        with open(self.bootstrap_path, "r") as f:
            self.bootstrap_data = json.load(f)

        # Room UUID to name mapping
        self.room_names = {
            room["id"]: room["name"] for room in self.bootstrap_data["scene"]["rooms"]
        }

        # Room color scheme for better visualization
        self.room_colors = {
            "550e8400-e29b-41d4-a716-446655441001": "#E8F4FD",  # Living Room - Light Blue
            "550e8400-e29b-41d4-a716-446655441002": "#FFF2E8",  # Kitchen - Light Orange
            "550e8400-e29b-41d4-a716-446655441003": "#F0E8FF",  # Master Bedroom - Light Purple
            "550e8400-e29b-41d4-a716-446655441004": "#E8FFE8",  # Second Bedroom - Light Green
            "550e8400-e29b-41d4-a716-446655441005": "#FFE8E8",  # Bathroom - Light Pink
            "550e8400-e29b-41d4-a716-446655441006": "#F8F8F8",  # Hallway - Light Gray
        }

        super().__init__(scene_graph, bus, agents)

        # Update window title and size for apartment
        self.root.title("SpacXT - Complex Apartment Visualizer")
        self.root.geometry("1400x900")

    def _create_widgets(self):
        """Create enhanced UI layout for apartment scene."""
        super()._create_widgets()

        # Add apartment-specific controls
        self._add_apartment_controls()

    def _add_apartment_controls(self):
        """Add apartment-specific control buttons."""
        # Find the controls frame
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):  # Right frame
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.LabelFrame) and "Controls" in grandchild.cget("text"):
                                # Add apartment controls
                                apt_frame = ttk.LabelFrame(grandchild, text="Apartment Actions", padding=3)
                                apt_frame.pack(fill=tk.X, pady=(5, 2))

                                # Export button
                                export_btn = ttk.Button(apt_frame, text="Export Scene",
                                                      command=self._export_scene)
                                export_btn.pack(side=tk.LEFT, padx=2)

                                # Room info button
                                room_btn = ttk.Button(apt_frame, text="Room Info",
                                                    command=self._show_room_info)
                                room_btn.pack(side=tk.LEFT, padx=2)

                                # Statistics button
                                stats_btn = ttk.Button(apt_frame, text="Statistics",
                                                     command=self._show_statistics)
                                stats_btn.pack(side=tk.LEFT, padx=2)

                                return

    def _setup_3d_plot(self):
        """Enhanced 3D plot setup for apartment visualization."""
        super()._setup_3d_plot()

        # Adjust view for apartment layout
        self.ax_3d.set_xlim(-1, 11)
        self.ax_3d.set_ylim(-1, 10)
        self.ax_3d.set_zlim(0, 3.5)

        # Better viewing angle for apartment
        self.ax_3d.view_init(elev=20, azim=45)

    def _draw_3d_scene(self):
        """Enhanced 3D scene drawing with room visualization."""
        self.ax_3d.clear()

        # Draw room boundaries first
        self._draw_room_boundaries()

        # Draw objects with enhanced styling
        self._draw_objects_enhanced()

        # Draw relationships
        self._draw_relationships_3d()

        # Enhanced labels and legend
        self._add_enhanced_labels()

        # Update plot
        self.ax_3d.set_xlim(-1, 11)
        self.ax_3d.set_ylim(-1, 10)
        self.ax_3d.set_zlim(0, 3.5)
        self.ax_3d.set_xlabel('X (meters)')
        self.ax_3d.set_ylabel('Y (meters)')
        self.ax_3d.set_zlabel('Z (meters)')
        self.ax_3d.set_title('Complex Apartment - Spatial Relationships')

        self.canvas_3d.draw()

    def _draw_room_boundaries(self):
        """Draw room boundaries as floor rectangles."""
        for room in self.bootstrap_data["scene"]["rooms"]:
            bbox = room["bbox"]
            min_coords = bbox["min"]
            max_coords = bbox["max"]

            # Room floor rectangle
            x_coords = [min_coords[0], max_coords[0], max_coords[0], min_coords[0], min_coords[0]]
            y_coords = [min_coords[1], min_coords[1], max_coords[1], max_coords[1], min_coords[1]]
            z_coords = [0.01] * 5  # Slightly above floor

            color = self.room_colors.get(room["id"], "#F0F0F0")

            # Draw floor
            vertices = [(x_coords[i], y_coords[i], z_coords[i]) for i in range(4)]
            collection = Poly3DCollection([vertices], facecolors=color, alpha=0.3, edgecolors='gray')
            self.ax_3d.add_collection3d(collection)

            # Room label
            center_x = (min_coords[0] + max_coords[0]) / 2
            center_y = (min_coords[1] + max_coords[1]) / 2
            self.ax_3d.text(center_x, center_y, 0.1, room["name"],
                           fontsize=8, ha='center', weight='bold', color='darkblue')

    def _draw_objects_enhanced(self):
        """Draw objects with enhanced visualization."""
        for node_id, node in self.graph.nodes.items():
            pos = node.pos
            bbox_size = node.bbox.get('xyz', [0.5, 0.5, 0.5])

            # Object color based on class
            color = self._get_object_color(node.cls)

            # Draw 3D box
            self._draw_3d_box(pos, bbox_size, color, alpha=0.7)

            # Enhanced label with name
            label = getattr(node, 'name', node.cls.title()) if hasattr(node, 'name') and node.name else node.cls.title()
            self.ax_3d.text(pos[0], pos[1], pos[2] + bbox_size[2]/2 + 0.1,
                           label, fontsize=6, ha='center', color='black')

    def _get_object_color(self, obj_class):
        """Get color for object based on its class."""
        color_map = {
            'sofa': '#8B4513',      # Brown
            'table': '#DEB887',     # Burlywood
            'tv_stand': '#696969',  # DimGray
            'tv': '#000000',        # Black
            'counter': '#D2691E',   # Chocolate
            'refrigerator': '#FFFFFF', # White
            'stove': '#C0C0C0',     # Silver
            'chair': '#CD853F',     # Peru
            'bed': '#4682B4',       # SteelBlue
            'nightstand': '#8B7355', # Brown4
            'wardrobe': '#8B4513',  # Brown
            'desk': '#DEB887',      # Burlywood
            'toilet': '#FFFFFF',    # White
            'sink': '#E6E6FA',      # Lavender
            'shower': '#E0E0E0',    # LightGray
            'wall': '#A0A0A0',      # Gray
            'door': '#8B4513',      # Brown
        }
        return color_map.get(obj_class, '#808080')  # Default gray

    def _draw_3d_box(self, center, size, color, alpha=0.7):
        """Draw a 3D box at the given position."""
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        x, y, z = center
        dx, dy, dz = size

        # Define the vertices of the box
        vertices = [
            [x-dx/2, y-dy/2, z-dz/2], [x+dx/2, y-dy/2, z-dz/2],
            [x+dx/2, y+dy/2, z-dz/2], [x-dx/2, y+dy/2, z-dz/2],
            [x-dx/2, y-dy/2, z+dz/2], [x+dx/2, y-dy/2, z+dz/2],
            [x+dx/2, y+dy/2, z+dz/2], [x-dx/2, y+dy/2, z+dz/2]
        ]

        # Define the 6 faces of the box
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
        ]

        # Create and add the collection
        collection = Poly3DCollection(faces, facecolors=color, alpha=alpha, edgecolors='black')
        self.ax_3d.add_collection3d(collection)

    def _draw_relationships_3d(self):
        """Draw spatial relationships in 3D."""
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a not in self.graph.nodes or b not in self.graph.nodes:
                continue

            # Skip room relationships for cleaner view
            if rel_type == 'in':
                continue

            node_a = self.graph.nodes[a]
            node_b = self.graph.nodes[b]

            # Line style based on relationship type
            if rel_type == 'beside':
                color, style, width = 'green', '-', 2
            elif rel_type == 'on_top_of':
                color, style, width = 'red', '-', 3
            elif rel_type == 'above' or rel_type == 'below':
                color, style, width = 'blue', '--', 1
            else:
                color, style, width = 'gray', ':', 1

            # Draw line
            self.ax_3d.plot([node_a.pos[0], node_b.pos[0]],
                           [node_a.pos[1], node_b.pos[1]],
                           [node_a.pos[2], node_b.pos[2]],
                           color=color, linestyle=style, linewidth=width, alpha=0.6)

    def _add_enhanced_labels(self):
        """Add enhanced labels and legend."""
        # Create legend for relationship types
        legend_elements = [
            plt.Line2D([0], [0], color='green', lw=2, label='Beside'),
            plt.Line2D([0], [0], color='red', lw=3, label='On Top Of'),
            plt.Line2D([0], [0], color='blue', lw=1, linestyle='--', label='Above/Below'),
        ]
        self.ax_3d.legend(handles=legend_elements, loc='upper right')

    def _export_scene(self):
        """Export the current scene with relationships."""
        try:
            from complex_apartment_demo import SceneExporter

            exporter = SceneExporter(self.graph)
            export_path = Path(__file__).parent / "apartment_gui_export.json"

            exported_data = exporter.export_scene_with_relationships(str(export_path))

            messagebox.showinfo("Export Complete",
                              f"Scene exported successfully!\n\n"
                              f"File: {export_path.name}\n"
                              f"Objects: {exported_data['scene']['export_metadata']['total_objects']}\n"
                              f"Relationships: {exported_data['scene']['export_metadata']['total_relationships']}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export scene:\n{str(e)}")

    def _show_room_info(self):
        """Show information about rooms and their contents."""
        info_window = tk.Toplevel(self.root)
        info_window.title("Room Information")
        info_window.geometry("600x400")

        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Generate room information
        info_text = "🏠 COMPLEX APARTMENT ROOM INFORMATION\n"
        info_text += "=" * 50 + "\n\n"

        for room in self.bootstrap_data["scene"]["rooms"]:
            room_id = room["id"]
            room_name = room["name"]
            bbox = room["bbox"]

            # Calculate room dimensions
            width = bbox["max"][0] - bbox["min"][0]
            height = bbox["max"][1] - bbox["min"][1]
            area = width * height

            info_text += f"📍 {room_name}\n"
            info_text += f"   UUID: {room_id}\n"
            info_text += f"   Dimensions: {width}m × {height}m ({area} sqm)\n"

            # Count objects in this room
            objects_in_room = []
            for (rel_type, a, b), relation in self.graph.relations.items():
                if rel_type == 'in' and b == room_id:
                    node = self.graph.nodes.get(a)
                    if node:
                        name = getattr(node, 'name', node.cls.title()) if hasattr(node, 'name') and node.name else node.cls.title()
                        objects_in_room.append(name)

            info_text += f"   Objects: {len(objects_in_room)}\n"
            for obj_name in sorted(objects_in_room):
                info_text += f"     • {obj_name}\n"
            info_text += "\n"

        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

    def _show_statistics(self):
        """Show scene statistics."""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Scene Statistics")
        stats_window.geometry("500x600")

        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Generate statistics
        stats_text = "📊 SCENE STATISTICS\n"
        stats_text += "=" * 30 + "\n\n"

        # Basic counts
        stats_text += f"🏠 Scene: {self.bootstrap_data['scene']['name']}\n"
        stats_text += f"📐 Total Area: ~80 square meters\n"
        stats_text += f"🚪 Rooms: {len(self.bootstrap_data['scene']['rooms'])}\n"
        stats_text += f"📦 Objects: {len(self.graph.nodes)}\n"
        stats_text += f"🔗 Relationships: {len(self.graph.relations)}\n"
        stats_text += f"🤖 Agents: {len(self.agents)}\n\n"

        # Object breakdown by class
        obj_classes = {}
        for node in self.graph.nodes.values():
            cls = node.cls
            obj_classes[cls] = obj_classes.get(cls, 0) + 1

        stats_text += "📋 OBJECTS BY TYPE\n"
        stats_text += "-" * 20 + "\n"
        for cls, count in sorted(obj_classes.items()):
            stats_text += f"{cls.title()}: {count}\n"

        # Relationship breakdown
        rel_types = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        stats_text += "\n🔗 RELATIONSHIPS BY TYPE\n"
        stats_text += "-" * 25 + "\n"
        for rel_type, count in sorted(rel_types.items()):
            stats_text += f"{rel_type.title()}: {count}\n"

        # Confidence distribution
        confidences = [rel.conf for rel in self.graph.relations.values()]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)

            stats_text += f"\n📈 CONFIDENCE SCORES\n"
            stats_text += "-" * 20 + "\n"
            stats_text += f"Average: {avg_conf:.2f}\n"
            stats_text += f"Range: {min_conf:.2f} - {max_conf:.2f}\n"

        text_widget.insert(tk.END, stats_text)
        text_widget.config(state=tk.DISABLED)


def main():
    """Run the complex apartment GUI demo."""
    print("🏠 Starting Complex Apartment GUI Demo...")

    try:
        # 1) Load bootstrap data
        bootstrap_path = Path(__file__).parent / "complex_apartment.json"
        with open(bootstrap_path, "r") as f:
            data = json.load(f)
        print(f"✅ Loaded scene: {data['scene']['name']}")

        # 2) Initialize scene graph
        graph = SceneGraph()
        graph.load_bootstrap(data)
        print(f"✅ Initialized scene with {len(graph.nodes)} objects in {len(data['scene']['rooms'])} rooms")

        # 3) Create message bus and agents
        bus = Bus()
        agent_ids = [obj["id"] for obj in data["scene"]["objects"]]
        agents = make_agents(graph, bus, agent_ids)
        print(f"✅ Created {len(agents)} agents")

        # 4) Launch enhanced GUI
        print("🎯 Launching complex apartment visualizer...")
        visualizer = ComplexApartmentVisualizer(graph, bus, agents)
        visualizer.run()

    except FileNotFoundError:
        print("❌ Error: complex_apartment.json not found")
        print("   Make sure you're running this from the examples/ directory")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        print("\n💡 Common fixes:")
        print("   - Make sure you have matplotlib and numpy installed: poetry install")
        print("   - Try running with: poetry run python complex_apartment_gui.py")
        print("   - Check that you're in the examples/ directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
