"""
3D Scene Visualizer for SpacXT - Real-time visualization of spatial relationships.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as patches
import numpy as np
import threading
import time
from typing import Dict, List, Any, Optional
import networkx as nx

from ..core.graph_store import SceneGraph, Node, Relation, GraphPatch
from ..core.orchestrator import Bus, make_agents, tick


class SceneVisualizer:
    def __init__(self, scene_graph: SceneGraph, bus: Bus, agents: Dict[str, Any]):
        self.graph = scene_graph
        self.bus = bus
        self.agents = agents
        self.running = False

        # Create main window
        self.root = tk.Tk()
        self.root.title("SpacXT - Spatial Context Visualizer")
        self.root.geometry("1200x800")

        # Animation state
        self.animation_thread = None

        # Graph layout cache for stable visualization
        self.graph_layout_cache = {}
        self.last_graph_signature = None

        # Create UI components
        self._create_widgets()
        self._setup_3d_plot()

    def _create_widgets(self):
        """Create the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - visualizations
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Top-left: 3D Scene View
        scene_3d_frame = ttk.LabelFrame(left_frame, text="3D Scene View", padding=5)
        scene_3d_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Bottom-left: Graph View
        graph_frame = ttk.LabelFrame(left_frame, text="Spatial Relationship Graph", padding=5)
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Right panel - controls and info
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Controls
        controls_frame = ttk.LabelFrame(right_frame, text="Controls", padding=5)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        self.start_btn = ttk.Button(controls_frame, text="Start Simulation",
                                   command=self._toggle_simulation)
        self.start_btn.pack(fill=tk.X, pady=2)

        self.step_btn = ttk.Button(controls_frame, text="Single Step",
                                  command=self._single_step)
        self.step_btn.pack(fill=tk.X, pady=2)

        self.reset_btn = ttk.Button(controls_frame, text="Reset Scene",
                                   command=self._reset_scene)
        self.reset_btn.pack(fill=tk.X, pady=2)

        # Move chair button
        self.move_btn = ttk.Button(controls_frame, text="Move Chair",
                                  command=self._move_chair)
        self.move_btn.pack(fill=tk.X, pady=2)

        # Relations panel
        relations_frame = ttk.LabelFrame(right_frame, text="Spatial Relations", padding=5)
        relations_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        self.relations_text = scrolledtext.ScrolledText(relations_frame,
                                                       width=30, height=10,
                                                       font=("Consolas", 10))
        self.relations_text.pack(fill=tk.BOTH, expand=True)

        # Agent activity panel
        activity_frame = ttk.LabelFrame(right_frame, text="Agent Activity", padding=5)
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.activity_text = scrolledtext.ScrolledText(activity_frame,
                                                      width=30, height=8,
                                                      font=("Consolas", 9))
        self.activity_text.pack(fill=tk.BOTH, expand=True)

        # Store frame references
        self.scene_3d_frame = scene_3d_frame
        self.graph_frame = graph_frame

    def _setup_3d_plot(self):
        """Initialize the 3D matplotlib plot and graph view."""
        # 3D Scene Plot
        self.fig_3d = plt.Figure(figsize=(8, 4))
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')

        # Configure 3D plot
        self.ax_3d.set_xlabel('X (meters)')
        self.ax_3d.set_ylabel('Y (meters)')
        self.ax_3d.set_zlabel('Z (meters)')
        self.ax_3d.set_title('3D Scene with Ground Reference')

        # Set equal aspect ratio and limits
        self.ax_3d.set_xlim(0, 5)
        self.ax_3d.set_ylim(0, 3)
        self.ax_3d.set_zlim(0, 2)

        # Embed 3D plot in tkinter
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, self.scene_3d_frame)
        self.canvas_3d.draw()
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Graph View Plot
        self.fig_graph = plt.Figure(figsize=(8, 4))
        self.ax_graph = self.fig_graph.add_subplot(111)

        # Configure graph plot
        self.ax_graph.set_title('Spatial Relationship Network')
        self.ax_graph.set_aspect('equal')
        self.ax_graph.axis('off')  # Hide axes for cleaner graph view

        # Embed graph plot in tkinter
        self.canvas_graph = FigureCanvasTkAgg(self.fig_graph, self.graph_frame)
        self.canvas_graph.draw()
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial render
        self._update_displays()

    def _create_box(self, center, size, color='blue', alpha=0.7):
        """Create a 3D box for visualization."""
        x, y, z = center
        dx, dy, dz = size

        # Define the vertices of a box
        vertices = [
            [x-dx/2, y-dy/2, z-dz/2],
            [x+dx/2, y-dy/2, z-dz/2],
            [x+dx/2, y+dy/2, z-dz/2],
            [x-dx/2, y+dy/2, z-dz/2],
            [x-dx/2, y-dy/2, z+dz/2],
            [x+dx/2, y-dy/2, z+dz/2],
            [x+dx/2, y+dy/2, z+dz/2],
            [x-dx/2, y+dy/2, z+dz/2]
        ]

        # Define the 6 faces of the box
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[2], vertices[3], vertices[7], vertices[6]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]]
        ]

        return Poly3DCollection(faces, facecolors=color, alpha=alpha, edgecolors='black')

    def _draw_ground_plane(self):
        """Draw a ground plane for spatial reference."""
        # Create ground plane mesh
        x = np.linspace(0, 5, 11)
        y = np.linspace(0, 3, 7)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)

        # Draw ground as wireframe
        self.ax_3d.plot_wireframe(X, Y, Z, color='lightgray', alpha=0.3, linewidth=0.5)

        # Add grid lines for better spatial reference
        for i in range(0, 6):
            self.ax_3d.plot([i, i], [0, 3], [0, 0], 'lightgray', alpha=0.5, linewidth=0.5)
        for j in range(0, 4):
            self.ax_3d.plot([0, 5], [j, j], [0, 0], 'lightgray', alpha=0.5, linewidth=0.5)

    def _update_3d_view(self):
        """Update the 3D visualization."""
        self.ax_3d.clear()

        # Configure plot again after clear
        self.ax_3d.set_xlabel('X (meters)')
        self.ax_3d.set_ylabel('Y (meters)')
        self.ax_3d.set_zlabel('Z (meters)')
        self.ax_3d.set_title('3D Scene with Ground Reference')
        self.ax_3d.set_xlim(0, 5)
        self.ax_3d.set_ylim(0, 3)
        self.ax_3d.set_zlim(0, 2)

        # Draw ground plane
        self._draw_ground_plane()

        # Color mapping for object types
        colors = {
            'table': 'brown',
            'chair': 'orange',
            'stove': 'red'
        }

        # Draw objects
        for node_id, node in self.graph.nodes.items():
            color = colors.get(node.cls, 'gray')
            size = node.bbox['xyz']

            # Adjust object position to sit on ground (z = size[2]/2)
            adjusted_pos = (node.pos[0], node.pos[1], size[2]/2)

            box = self._create_box(adjusted_pos, size, color=color)
            self.ax_3d.add_collection3d(box)

            # Add labels above objects
            self.ax_3d.text(adjusted_pos[0], adjusted_pos[1], adjusted_pos[2] + size[2]/2 + 0.1,
                           f"{node.id}\n({node.cls})",
                           fontsize=8, ha='center')

        # Draw relationships as lines
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a in self.graph.nodes and b in self.graph.nodes:
                node_a = self.graph.nodes[a]
                node_b = self.graph.nodes[b]

                # Skip "in" relationships for cleaner view
                if rel_type == "in":
                    continue

                # Adjust positions for ground-sitting objects
                size_a = node_a.bbox['xyz']
                size_b = node_b.bbox['xyz']
                pos_a = (node_a.pos[0], node_a.pos[1], size_a[2]/2)
                pos_b = (node_b.pos[0], node_b.pos[1], size_b[2]/2)

                # Draw line between objects
                self.ax_3d.plot([pos_a[0], pos_b[0]],
                               [pos_a[1], pos_b[1]],
                               [pos_a[2], pos_b[2]],
                               'g--', alpha=0.6, linewidth=2)

                # Add relationship label
                mid_x = (pos_a[0] + pos_b[0]) / 2
                mid_y = (pos_a[1] + pos_b[1]) / 2
                mid_z = (pos_a[2] + pos_b[2]) / 2
                self.ax_3d.text(mid_x, mid_y, mid_z, f"{rel_type}\n{relation.conf:.2f}",
                               fontsize=7, color='green', ha='center',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

        self.canvas_3d.draw()

    def _update_graph_view(self):
        """Update the network graph visualization."""
        self.ax_graph.clear()

        # Configure graph plot
        self.ax_graph.set_title('Spatial Relationship Network')
        self.ax_graph.set_aspect('equal')
        self.ax_graph.axis('off')

        # Create NetworkX graph
        G = nx.Graph()

        # Add nodes (objects)
        for node_id, node in self.graph.nodes.items():
            G.add_node(node_id, cls=node.cls, pos=node.pos)

        # Add edges (spatial relationships)
        edge_labels = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a in self.graph.nodes and b in self.graph.nodes:
                # Skip "in" relationships for cleaner graph view
                if rel_type == "in":
                    continue

                G.add_edge(a, b, relation=rel_type, confidence=relation.conf)
                edge_labels[(a, b)] = f"{rel_type}\n{relation.conf:.2f}"

        if len(G.nodes) == 0:
            self.ax_graph.text(0.5, 0.5, "No objects in scene",
                              transform=self.ax_graph.transAxes,
                              ha='center', va='center', fontsize=12)
            self.canvas_graph.draw()
            return

        # Create a signature for the current graph structure
        nodes_signature = tuple(sorted(G.nodes))
        edges_signature = tuple(sorted(G.edges))
        graph_signature = (nodes_signature, edges_signature)

        # Only recalculate layout if graph structure changed
        if graph_signature != self.last_graph_signature:
            try:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)  # Fixed seed for consistency
            except:
                # Fallback if spring layout fails
                pos = {node: (i*0.3, 0) for i, node in enumerate(G.nodes)}

            # Cache the new layout and signature
            self.graph_layout_cache = pos
            self.last_graph_signature = graph_signature
        else:
            # Use cached layout - no animation
            pos = self.graph_layout_cache

        # Color mapping for object types
        node_colors = {
            'table': 'brown',
            'chair': 'orange',
            'stove': 'red'
        }

        # Draw nodes
        for node, (x, y) in pos.items():
            node_data = self.graph.nodes[node]
            color = node_colors.get(node_data.cls, 'gray')

            # Draw node as circle
            circle = plt.Circle((x, y), 0.1, color=color, alpha=0.7, zorder=2)
            self.ax_graph.add_patch(circle)

            # Add node label
            self.ax_graph.text(x, y-0.15, f"{node}\n({node_data.cls})",
                              ha='center', va='top', fontsize=8, zorder=3)

        # Draw edges (relationships)
        for (a, b), label in edge_labels.items():
            if a in pos and b in pos:
                x1, y1 = pos[a]
                x2, y2 = pos[b]

                # Draw edge line
                self.ax_graph.plot([x1, x2], [y1, y2], 'g-', alpha=0.6, linewidth=2, zorder=1)

                # Add edge label
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                self.ax_graph.text(mid_x, mid_y, label, ha='center', va='center',
                                  fontsize=7, color='green', zorder=3,
                                  bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))

        # Set equal aspect and adjust limits
        if pos:
            x_coords = [x for x, y in pos.values()]
            y_coords = [y for x, y in pos.values()]
            margin = 0.3
            self.ax_graph.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
            self.ax_graph.set_ylim(min(y_coords) - margin, max(y_coords) + margin)

        self.canvas_graph.draw()

    def _update_relations_panel(self):
        """Update the relations text panel."""
        self.relations_text.delete(1.0, tk.END)

        relations_by_type = {}
        for (rel_type, a, b), relation in self.graph.relations.items():
            if rel_type not in relations_by_type:
                relations_by_type[rel_type] = []
            relations_by_type[rel_type].append((a, b, relation.conf))

        for rel_type, relations in relations_by_type.items():
            self.relations_text.insert(tk.END, f"=== {rel_type.upper()} ===\n")
            for a, b, conf in relations:
                self.relations_text.insert(tk.END, f"  {a} → {b} (conf: {conf:.2f})\n")
            self.relations_text.insert(tk.END, "\n")

    def _log_activity(self, message: str):
        """Log agent activity."""
        self.activity_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} {message}\n")
        self.activity_text.see(tk.END)

        # Keep only last 100 lines
        lines = self.activity_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.activity_text.delete(1.0, tk.END)
            self.activity_text.insert(1.0, '\n'.join(lines[-100:]))

    def _toggle_simulation(self):
        """Start/stop the simulation."""
        if not self.running:
            self.running = True
            self.start_btn.config(text="Stop Simulation")
            self._log_activity("🚀 Starting simulation...")

            # Start simulation thread
            self.animation_thread = threading.Thread(target=self._simulation_loop)
            self.animation_thread.daemon = True
            self.animation_thread.start()
        else:
            self.running = False
            self.start_btn.config(text="Start Simulation")
            self._log_activity("⏹️ Simulation stopped")

    def _simulation_loop(self):
        """Main simulation loop running in separate thread."""
        step_count = 0
        while self.running:
            try:
                # Run one tick
                tick(self.graph, self.bus, self.agents)
                step_count += 1

                # Log more detailed activity
                non_in_relations = [r for r in self.graph.relations.keys() if r[0] != "in"]
                rel_count = len(non_in_relations)
                msg_count = sum(len(self.bus.queues[aid]) for aid in self.agents.keys())

                # Update UI in main thread
                self.root.after(0, self._update_displays)
                if rel_count > 0:
                    self.root.after(0, lambda s=step_count, r=rel_count:
                        self._log_activity(f"🎉 Tick {s} | New spatial relations discovered! Total: {r}"))
                else:
                    self.root.after(0, lambda s=step_count, m=msg_count:
                        self._log_activity(f"Tick {s} | Negotiating... (Messages: {m})"))

                time.sleep(0.5)  # 2 ticks per second

            except Exception as e:
                self.root.after(0, lambda: self._log_activity(f"❌ Error: {str(e)}"))
                break

    def _single_step(self):
        """Run a single simulation step."""
        try:
            tick(self.graph, self.bus, self.agents)
            self._update_displays()
            self._log_activity("Single step completed")
        except Exception as e:
            self._log_activity(f"❌ Error: {str(e)}")

    def _move_chair(self):
        """Move the chair to a new position."""
        try:
            # Move chair closer to stove
            patch = GraphPatch()
            patch.update_nodes["chair_12"] = {"pos": (2.8, 1.3, 0.45)}
            self.graph.apply_patch(patch)

            self._update_displays()
            self._log_activity("📦 Moved chair to new position")

        except Exception as e:
            self._log_activity(f"❌ Move error: {str(e)}")

    def _reset_scene(self):
        """Reset the scene to initial state."""
        try:
            # Stop simulation
            self.running = False
            self.start_btn.config(text="Start Simulation")

            # Reset chair position
            patch = GraphPatch()
            patch.update_nodes["chair_12"] = {"pos": (1.8, 2.1, 0.45)}
            self.graph.apply_patch(patch)

            # Clear non-bootstrap relations
            keys_to_remove = []
            for key, relation in self.graph.relations.items():
                if key[0] not in ["in"]:  # Keep only "in" relations
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.graph.relations[key]

            self._update_displays()
            self._log_activity("🔄 Scene reset to initial state")

        except Exception as e:
            self._log_activity(f"❌ Reset error: {str(e)}")

    def _update_displays(self):
        """Update all display components."""
        self._update_3d_view()
        self._update_graph_view()
        self._update_relations_panel()

    def run(self):
        """Start the GUI application."""
        self._log_activity("🎯 SpacXT Visualizer initialized")
        self._log_activity("💡 Use controls to interact with the scene")
        self._update_displays()
        self.root.mainloop()

    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'running'):
            self.running = False
