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
from ..nlp.llm_parser import LLMCommandParser
from ..nlp.scene_modifier import SceneModifier


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

        # Natural language processing
        self.command_parser = LLMCommandParser()
        self.scene_modifier = SceneModifier(scene_graph, bus, agents)

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

        # 3D View Controls
        view_frame = ttk.LabelFrame(controls_frame, text="3D View Controls", padding=3)
        view_frame.pack(fill=tk.X, pady=(5, 2))

        # Zoom controls
        zoom_frame = ttk.Frame(view_frame)
        zoom_frame.pack(fill=tk.X)

        self.zoom_in_btn = ttk.Button(zoom_frame, text="Zoom In",
                                     command=self._zoom_in, width=8)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)

        self.zoom_out_btn = ttk.Button(zoom_frame, text="Zoom Out",
                                      command=self._zoom_out, width=8)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self.reset_view_btn = ttk.Button(zoom_frame, text="Reset View",
                                        command=self._reset_view, width=8)
        self.reset_view_btn.pack(side=tk.LEFT, padx=2)

        # Physics status (no manual buttons needed)
        physics_frame = ttk.Frame(view_frame)
        physics_frame.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(physics_frame, text="🌍 Automatic Physics: Always Active",
                 font=("Consolas", 9), foreground="green").pack()

        # View info
        ttk.Label(view_frame, text="💡 Mouse: Left=Rotate, Right=Pan, Wheel=Zoom",
                 font=("Consolas", 8), foreground="gray").pack(pady=(2, 0))

        # AI Chat Interface
        chat_frame = ttk.LabelFrame(right_frame, text="AI Assistant", padding=5)
        chat_frame.pack(fill=tk.X, pady=(5, 5))

        # Chat history display
        self.chat_history = scrolledtext.ScrolledText(chat_frame,
                                                     width=40, height=8,
                                                     font=("Consolas", 9),
                                                     wrap=tk.WORD,
                                                     state=tk.DISABLED)
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Configure chat history tags for styling
        self.chat_history.tag_configure("user", foreground="blue", font=("Consolas", 9, "bold"))
        self.chat_history.tag_configure("assistant", foreground="darkgreen")
        self.chat_history.tag_configure("system", foreground="gray", font=("Consolas", 8, "italic"))
        self.chat_history.tag_configure("error", foreground="red")
        self.chat_history.tag_configure("success", foreground="green")

        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(0, 2))

        # Command input field
        self.command_entry = tk.Text(input_frame, height=2, font=("Consolas", 10), wrap=tk.WORD)
        self.command_entry.pack(fill=tk.X, pady=(0, 5))
        self.command_entry.bind('<Control-Return>', self._execute_command)
        self.command_entry.bind('<Shift-Return>', self._execute_command)

        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)

        # Execute button with loading state
        self.execute_btn = ttk.Button(button_frame, text="Send (Ctrl+Enter)",
                                     command=self._execute_command)
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Clear chat button
        self.clear_chat_btn = ttk.Button(button_frame, text="Clear Chat",
                                        command=self._clear_chat)
        self.clear_chat_btn.pack(side=tk.LEFT)

        # Processing indicator
        self.processing_label = ttk.Label(button_frame, text="", font=("Consolas", 8))
        self.processing_label.pack(side=tk.RIGHT)

        # Initialize chat
        self._add_chat_message("system", "Welcome! I can help you manipulate the 3D scene using natural language.")
        self._add_chat_message("system", "Examples: 'put a cup on the table', 'move the chair', 'add a book'")

        # Chat processing state
        self.chat_processing = False

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
        self.ax_3d.set_title('3D Scene (Mouse: Rotate/Pan/Zoom)')

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
        self.ax_graph.set_title('Spatial Relationship Network (Mouse: Pan/Zoom)')
        self.ax_graph.set_aspect('equal')
        self.ax_graph.axis('off')  # Hide axes for cleaner graph view

        # Graph view state
        self.graph_zoom_level = 1.0
        self.graph_xlim = None
        self.graph_ylim = None

        # Embed graph plot in tkinter
        self.canvas_graph = FigureCanvasTkAgg(self.fig_graph, self.graph_frame)
        self.canvas_graph.draw()
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add graph controls
        graph_controls_frame = ttk.Frame(self.graph_frame)
        graph_controls_frame.pack(fill=tk.X, pady=(2, 0))

        # Graph control buttons
        self.graph_zoom_in_btn = ttk.Button(graph_controls_frame, text="🔍+",
                                           command=self._graph_zoom_in, width=4)
        self.graph_zoom_in_btn.pack(side=tk.LEFT, padx=2)

        self.graph_zoom_out_btn = ttk.Button(graph_controls_frame, text="🔍-",
                                            command=self._graph_zoom_out, width=4)
        self.graph_zoom_out_btn.pack(side=tk.LEFT, padx=2)

        self.graph_reset_btn = ttk.Button(graph_controls_frame, text="🔄",
                                         command=self._graph_reset_view, width=4)
        self.graph_reset_btn.pack(side=tk.LEFT, padx=2)

        self.graph_rearrange_btn = ttk.Button(graph_controls_frame, text="⚡",
                                             command=self._graph_rearrange, width=4)
        self.graph_rearrange_btn.pack(side=tk.LEFT, padx=2)

        # Layout selector
        ttk.Label(graph_controls_frame, text="Layout:", font=("Consolas", 8)).pack(side=tk.LEFT, padx=(10, 2))
        self.layout_var = tk.StringVar(value="spring")
        self.layout_combo = ttk.Combobox(graph_controls_frame, textvariable=self.layout_var,
                                        values=["spring", "circular", "shell", "kamada_kawai"],
                                        width=10, font=("Consolas", 8))
        self.layout_combo.pack(side=tk.LEFT, padx=2)
        self.layout_combo.bind('<<ComboboxSelected>>', self._on_layout_change)

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
        self.ax_3d.set_title('3D Scene (Mouse: Rotate/Pan/Zoom)')
        self.ax_3d.set_xlim(0, 5)
        self.ax_3d.set_ylim(0, 3)
        self.ax_3d.set_zlim(0, 2)

        # Draw ground plane
        self._draw_ground_plane()

        # Color mapping for object types
        colors = {
            'table': 'brown', 'chair': 'orange', 'stove': 'red',
            'cup': 'lightblue', 'glass': 'lightcyan', 'plate': 'lightgray',
            'bowl': 'wheat', 'book': 'darkgreen', 'laptop': 'darkgray',
            'phone': 'black', 'lamp': 'gold', 'vase': 'purple',
            'candle': 'lightyellow', 'fruit': 'red', 'bottle': 'blue',
            'pen': 'darkblue', 'paper': 'white'
        }

        # Draw objects
        for node_id, node in self.graph.nodes.items():
            color = colors.get(node.cls, 'gray')
            size = node.bbox['xyz']

            # Ensure minimum size for visibility (avoid flat 2D appearance)
            min_size = 0.02
            size = [max(s, min_size) for s in size]

            # Adjust object position to sit on ground (z = size[2]/2)
            adjusted_pos = (node.pos[0], node.pos[1], node.pos[2])

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
                pos = self._calculate_graph_layout(G)
            except:
                # Fallback if layout calculation fails
                pos = {node: (i*0.5, (i%3)*0.5) for i, node in enumerate(G.nodes)}

            # Cache the new layout and signature
            self.graph_layout_cache = pos
            self.last_graph_signature = graph_signature
        else:
            # Use cached layout - no animation
            pos = self.graph_layout_cache

        # Color mapping for object types
        node_colors = {
            'table': 'brown', 'chair': 'orange', 'stove': 'red',
            'cup': 'lightblue', 'glass': 'lightcyan', 'plate': 'lightgray',
            'bowl': 'wheat', 'book': 'darkgreen', 'laptop': 'darkgray',
            'phone': 'black', 'lamp': 'gold', 'vase': 'purple',
            'candle': 'lightyellow', 'fruit': 'red', 'bottle': 'blue',
            'pen': 'darkblue', 'paper': 'white'
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

        # Set equal aspect and adjust limits with zoom support
        if pos:
            x_coords = [x for x, y in pos.values()]
            y_coords = [y for x, y in pos.values()]

            # Calculate base limits
            margin = 0.3
            base_xlim = (min(x_coords) - margin, max(x_coords) + margin)
            base_ylim = (min(y_coords) - margin, max(y_coords) + margin)

            # Apply zoom and custom limits if set
            if self.graph_xlim and self.graph_ylim:
                self.ax_graph.set_xlim(self.graph_xlim)
                self.ax_graph.set_ylim(self.graph_ylim)
            else:
                # Apply zoom to base limits
                x_center = (base_xlim[0] + base_xlim[1]) / 2
                y_center = (base_ylim[0] + base_ylim[1]) / 2
                x_range = (base_xlim[1] - base_xlim[0]) / (2 * self.graph_zoom_level)
                y_range = (base_ylim[1] - base_ylim[0]) / (2 * self.graph_zoom_level)

                self.ax_graph.set_xlim(x_center - x_range, x_center + x_range)
                self.ax_graph.set_ylim(y_center - y_range, y_center + y_range)

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
                error_msg = str(e)
                self.root.after(0, lambda: self._log_activity(f"❌ Error: {error_msg}"))
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

    def _add_chat_message(self, sender: str, message: str):
        """Add a message to the chat history."""
        self.chat_history.config(state=tk.NORMAL)

        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")

        if sender == "user":
            self.chat_history.insert(tk.END, f"[{timestamp}] You: ", "user")
            self.chat_history.insert(tk.END, f"{message}\n\n")
        elif sender == "assistant":
            self.chat_history.insert(tk.END, f"[{timestamp}] Assistant: ", "assistant")
            self.chat_history.insert(tk.END, f"{message}\n\n")
        elif sender == "system":
            self.chat_history.insert(tk.END, f"[{timestamp}] ", "system")
            self.chat_history.insert(tk.END, f"{message}\n", "system")
        elif sender == "error":
            self.chat_history.insert(tk.END, f"[{timestamp}] Error: ", "error")
            self.chat_history.insert(tk.END, f"{message}\n\n", "error")
        elif sender == "success":
            self.chat_history.insert(tk.END, f"[{timestamp}] ✅ ", "success")
            self.chat_history.insert(tk.END, f"{message}\n\n", "success")

        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

        # Keep chat history manageable (last 100 messages)
        lines = self.chat_history.get(1.0, tk.END).split('\n')
        if len(lines) > 200:  # Roughly 100 message pairs
            self.chat_history.config(state=tk.NORMAL)
            # Remove first 50 lines
            for _ in range(50):
                self.chat_history.delete(1.0, "2.0")
            self.chat_history.config(state=tk.DISABLED)

    def _clear_chat(self):
        """Clear the chat history."""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state=tk.DISABLED)
        self._add_chat_message("system", "Chat cleared. Ready for new commands!")

    def _set_processing_state(self, processing: bool):
        """Update the processing state and UI indicators."""
        self.chat_processing = processing

        if processing:
            self.execute_btn.config(text="Processing...", state="disabled")
            self.processing_label.config(text="🤔 Thinking...", foreground="orange")
        else:
            self.execute_btn.config(text="Send (Ctrl+Enter)", state="normal")
            self.processing_label.config(text="", foreground="black")

    def _execute_command(self, event=None):
        """Execute a natural language command in a separate thread."""
        if self.chat_processing:
            return

        # Get command text
        command_text = self.command_entry.get(1.0, tk.END).strip()
        if not command_text:
            return

        # Add user message to chat
        self._add_chat_message("user", command_text)

        # Clear input field
        self.command_entry.delete(1.0, tk.END)

        # Set processing state
        self._set_processing_state(True)

        # Execute command in background thread
        command_thread = threading.Thread(target=self._process_command, args=(command_text,))
        command_thread.daemon = True
        command_thread.start()

    def _process_command(self, command_text: str):
        """Process the command in a background thread."""
        try:
            # Build scene context for LLM
            scene_context = {"objects": self.graph.nodes}

            # Parse command (this is where LLM processing happens)
            parsed_command = self.command_parser.parse(command_text, scene_context)

            if not parsed_command:
                self.root.after(0, lambda: self._handle_command_result(False, "I couldn't understand that command. Could you try rephrasing it?"))
                return

            # Execute command
            success, message = self.scene_modifier.execute_command(parsed_command)

            if success:
                # Schedule UI updates in main thread
                self.root.after(0, lambda: self._handle_command_success(message, parsed_command))
            else:
                self.root.after(0, lambda: self._handle_command_result(False, message))

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._handle_command_result(False, f"An error occurred: {error_msg}"))

    def _handle_command_success(self, message: str, parsed_command):
        """Handle successful command execution in main thread."""
        try:
            # Add success message to chat
            assistant_response = f"Done! {message}"
            if hasattr(parsed_command, 'object_type') and hasattr(parsed_command, 'action'):
                assistant_response += f" (Action: {parsed_command.action} {parsed_command.object_type})"

            self._add_chat_message("assistant", assistant_response)

            # Update displays
            self._update_displays()

            # Log activity
            self._log_activity(f"✅ {message}")

            # Run a few ticks to let agents discover new relationships
            for _ in range(3):
                tick(self.graph, self.bus, self.scene_modifier.agents)

            # Update displays again
            self._update_displays()

        except Exception as e:
            self._add_chat_message("error", f"Error updating scene: {str(e)}")
        finally:
            self._set_processing_state(False)

    def _handle_command_result(self, success: bool, message: str):
        """Handle command result in main thread."""
        try:
            if success:
                self._add_chat_message("success", message)
                self._log_activity(f"✅ {message}")
            else:
                self._add_chat_message("error", message)
                self._log_activity(f"❌ {message}")
        finally:
            self._set_processing_state(False)

    def _zoom_in(self):
        """Zoom into the 3D view."""
        try:
            # Get current axis limits
            xlim = self.ax_3d.get_xlim()
            ylim = self.ax_3d.get_ylim()
            zlim = self.ax_3d.get_zlim()

            # Calculate zoom factor (zoom in by 20%)
            zoom_factor = 0.8

            # Calculate centers
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2

            # Calculate new ranges
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            z_range = (zlim[1] - zlim[0]) * zoom_factor / 2

            # Set new limits
            self.ax_3d.set_xlim(x_center - x_range, x_center + x_range)
            self.ax_3d.set_ylim(y_center - y_range, y_center + y_range)
            self.ax_3d.set_zlim(z_center - z_range, z_center + z_range)

            self.canvas_3d.draw()
            self._log_activity("🔍 Zoomed in")

        except Exception as e:
            self._log_activity(f"❌ Zoom error: {str(e)}")

    def _zoom_out(self):
        """Zoom out of the 3D view."""
        try:
            # Get current axis limits
            xlim = self.ax_3d.get_xlim()
            ylim = self.ax_3d.get_ylim()
            zlim = self.ax_3d.get_zlim()

            # Calculate zoom factor (zoom out by 25%)
            zoom_factor = 1.25

            # Calculate centers
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2

            # Calculate new ranges
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            z_range = (zlim[1] - zlim[0]) * zoom_factor / 2

            # Set new limits (with bounds checking)
            self.ax_3d.set_xlim(max(-1, x_center - x_range), min(6, x_center + x_range))
            self.ax_3d.set_ylim(max(-1, y_center - y_range), min(4, y_center + y_range))
            self.ax_3d.set_zlim(max(0, z_center - z_range), min(3, z_center + z_range))

            self.canvas_3d.draw()
            self._log_activity("🔍 Zoomed out")

        except Exception as e:
            self._log_activity(f"❌ Zoom error: {str(e)}")

    def _reset_view(self):
        """Reset 3D view to default position and zoom."""
        try:
            # Reset to original view limits
            self.ax_3d.set_xlim(0, 5)
            self.ax_3d.set_ylim(0, 3)
            self.ax_3d.set_zlim(0, 2)

            # Reset view angle to default
            self.ax_3d.view_init(elev=20, azim=45)

            self.canvas_3d.draw()
            self._log_activity("🔄 Reset 3D view")

        except Exception as e:
            self._log_activity(f"❌ View reset error: {str(e)}")

    def _calculate_graph_layout(self, G):
        """Calculate graph layout based on selected algorithm."""
        layout_type = self.layout_var.get()

        if layout_type == "spring":
            # If we have a previous layout and only nodes were added, use incremental layout
            current_nodes = set(G.nodes())
            previous_nodes = set(self.graph_layout_cache.keys()) if self.graph_layout_cache else set()

            if previous_nodes and current_nodes.issuperset(previous_nodes):
                # Only new nodes added - use incremental layout
                return nx.spring_layout(G, pos=self.graph_layout_cache, k=2, iterations=30, seed=42)
            else:
                # Major structural change - full recalculation with better spacing
                return nx.spring_layout(G, k=3, iterations=50, seed=42)

        elif layout_type == "circular":
            return nx.circular_layout(G)

        elif layout_type == "shell":
            return nx.shell_layout(G)

        elif layout_type == "kamada_kawai":
            if len(G.nodes) > 1:
                return nx.kamada_kawai_layout(G)
            else:
                return nx.spring_layout(G, k=3, iterations=50, seed=42)

        else:
            # Default to spring layout
            return nx.spring_layout(G, k=3, iterations=50, seed=42)

    def _graph_zoom_in(self):
        """Zoom into the graph view."""
        try:
            self.graph_zoom_level *= 1.5
            self.graph_xlim = None  # Reset custom limits to use zoom
            self.graph_ylim = None
            self._update_graph_view()
            self._log_activity("🔍 Graph zoomed in")
        except Exception as e:
            self._log_activity(f"❌ Graph zoom error: {str(e)}")

    def _graph_zoom_out(self):
        """Zoom out of the graph view."""
        try:
            self.graph_zoom_level /= 1.5
            self.graph_zoom_level = max(0.1, self.graph_zoom_level)  # Minimum zoom
            self.graph_xlim = None  # Reset custom limits to use zoom
            self.graph_ylim = None
            self._update_graph_view()
            self._log_activity("🔍 Graph zoomed out")
        except Exception as e:
            self._log_activity(f"❌ Graph zoom error: {str(e)}")

    def _graph_reset_view(self):
        """Reset graph view to default zoom and position."""
        try:
            self.graph_zoom_level = 1.0
            self.graph_xlim = None
            self.graph_ylim = None
            self._update_graph_view()
            self._log_activity("🔄 Graph view reset")
        except Exception as e:
            self._log_activity(f"❌ Graph reset error: {str(e)}")

    def _graph_rearrange(self):
        """Force rearrangement of the graph layout."""
        try:
            # Clear layout cache to force recalculation
            self.graph_layout_cache = {}
            self.last_graph_signature = None
            self._update_graph_view()
            self._log_activity("⚡ Graph layout refreshed")
        except Exception as e:
            self._log_activity(f"❌ Graph rearrange error: {str(e)}")

    def _on_layout_change(self, event=None):
        """Handle layout algorithm change."""
        try:
            # Clear cache and force recalculation with new layout
            self.graph_layout_cache = {}
            self.last_graph_signature = None
            self._update_graph_view()
            layout_name = self.layout_var.get()
            self._log_activity(f"📐 Changed to {layout_name} layout")
        except Exception as e:
            self._log_activity(f"❌ Layout change error: {str(e)}")


    def _update_displays(self):
        """Update all display components."""
        self._update_3d_view()
        self._update_graph_view()
        self._update_relations_panel()

    def run(self):
        """Start the GUI application."""
        self._log_activity("🎯 SpacXT Visualizer initialized")
        self._log_activity("💡 Use controls to interact with the scene")

        # Log auto-physics status
        if hasattr(self.graph, 'auto_physics') and self.graph.auto_physics:
            self._log_activity("🌍 Auto-physics enabled - objects snap to ground automatically")

        self._update_displays()
        self.root.mainloop()

    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'running'):
            self.running = False
