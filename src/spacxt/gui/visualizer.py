"""
3D Scene Visualizer for SpacXT - Real-time visualization of spatial relationships.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import threading
import time
from typing import Dict, List, Any, Optional

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

        # Create UI components
        self._create_widgets()
        self._setup_3d_plot()

        # Animation state
        self.animation_thread = None

    def _create_widgets(self):
        """Create the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - 3D visualization
        left_frame = ttk.LabelFrame(main_frame, text="3D Scene View", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

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

        # 3D plot container
        self.plot_frame = left_frame

    def _setup_3d_plot(self):
        """Initialize the 3D matplotlib plot."""
        self.fig = plt.Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')

        # Configure plot
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('3D Scene Graph')

        # Set equal aspect ratio and limits
        self.ax.set_xlim(0, 5)
        self.ax.set_ylim(0, 3)
        self.ax.set_zlim(0, 2)

        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial render
        self._update_3d_view()

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

    def _update_3d_view(self):
        """Update the 3D visualization."""
        self.ax.clear()

        # Configure plot again after clear
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('3D Scene Graph - SpacXT')
        self.ax.set_xlim(0, 5)
        self.ax.set_ylim(0, 3)
        self.ax.set_zlim(0, 2)

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

            box = self._create_box(node.pos, size, color=color)
            self.ax.add_collection3d(box)

            # Add labels
            self.ax.text(node.pos[0], node.pos[1], node.pos[2] + size[2]/2 + 0.1,
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

                # Draw line between objects
                self.ax.plot([node_a.pos[0], node_b.pos[0]],
                           [node_a.pos[1], node_b.pos[1]],
                           [node_a.pos[2], node_b.pos[2]],
                           'g--', alpha=0.6, linewidth=2)

                # Add relationship label
                mid_x = (node_a.pos[0] + node_b.pos[0]) / 2
                mid_y = (node_a.pos[1] + node_b.pos[1]) / 2
                mid_z = (node_a.pos[2] + node_b.pos[2]) / 2
                self.ax.text(mid_x, mid_y, mid_z, rel_type,
                           fontsize=7, color='green', ha='center')

        self.canvas.draw()

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
