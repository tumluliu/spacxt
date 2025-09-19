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

        # Scene controls
        scene_control_frame = ttk.LabelFrame(controls_frame, text="Scene Controls", padding=3)
        scene_control_frame.pack(fill=tk.X, pady=(5, 2))

        # Advanced simulation controls (optional)
        advanced_frame = ttk.LabelFrame(scene_control_frame, text="Advanced: Live Negotiation", padding=2)
        advanced_frame.pack(fill=tk.X, pady=(0, 2))

        self.start_btn = ttk.Button(advanced_frame, text="Start Live Negotiation",
                                   command=self._toggle_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.step_btn = ttk.Button(advanced_frame, text="Single Step",
                                  command=self._single_step)
        self.step_btn.pack(side=tk.LEFT, padx=2)

        # Info about intrinsic relationships
        ttk.Label(scene_control_frame, text="🧠 Spatial relationships are intrinsic to the 3D scene",
                 font=("Consolas", 8), foreground="darkgreen").pack(pady=(2, 0))
        ttk.Label(scene_control_frame, text="   Agent negotiations happen automatically on scene changes",
                 font=("Consolas", 8), foreground="gray").pack()

        self.reset_btn = ttk.Button(controls_frame, text="Reset Scene",
                                   command=self._reset_scene)
        self.reset_btn.pack(fill=tk.X, pady=2)

        # Move chair button
        self.move_btn = ttk.Button(controls_frame, text="Move Chair",
                                  command=self._move_chair)
        self.move_btn.pack(fill=tk.X, pady=2)

        # Physics status (no manual buttons needed)
        physics_frame = ttk.Frame(controls_frame)
        physics_frame.pack(fill=tk.X, pady=(5, 2))

        ttk.Label(physics_frame, text="🌍 Automatic Physics: Always Active",
                 font=("Consolas", 9), foreground="green").pack()

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
        self.fig_3d.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
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

        # Add 3D view controls at the bottom (compact layout)
        view_controls_frame = ttk.Frame(self.scene_3d_frame)
        view_controls_frame.pack(fill=tk.X, pady=(1, 0))

        # 3D control buttons (compact)
        controls_left = ttk.Frame(view_controls_frame)
        controls_left.pack(side=tk.LEFT)

        self.zoom_in_btn = ttk.Button(controls_left, text="🔍+",
                                     command=self._zoom_in, width=3)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=1)

        self.zoom_out_btn = ttk.Button(controls_left, text="🔍-",
                                      command=self._zoom_out, width=3)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=1)

        self.reset_view_btn = ttk.Button(controls_left, text="🔄",
                                        command=self._reset_view, width=3)
        self.reset_view_btn.pack(side=tk.LEFT, padx=1)

        # View info label (compact)
        ttk.Label(view_controls_frame, text="💡 Mouse: Rotate/Pan/Zoom",
                 font=("Consolas", 7), foreground="gray").pack(side=tk.RIGHT)

        # Graph View Plot
        self.fig_graph = plt.Figure(figsize=(8, 4))
        self.fig_graph.subplots_adjust(left=0.15, right=0.85, top=0.8, bottom=0.15)
        self.ax_graph = self.fig_graph.add_subplot(111)

        # Configure graph plot
        self.ax_graph.set_title('Directed Spatial Relationships (Mouse: Pan/Zoom/Drag)')
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

        # Enable built-in matplotlib navigation for graph
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.graph_toolbar = NavigationToolbar2Tk(self.canvas_graph, self.graph_frame)
        self.graph_toolbar.update()
        # Hide the toolbar but keep the functionality
        self.graph_toolbar.pack_forget()

        # Add graph controls (compact layout)
        graph_controls_frame = ttk.Frame(self.graph_frame)
        graph_controls_frame.pack(fill=tk.X, pady=(1, 0))

        # Left side controls
        controls_left = ttk.Frame(graph_controls_frame)
        controls_left.pack(side=tk.LEFT)

        # Graph control buttons (compact)
        self.graph_zoom_in_btn = ttk.Button(controls_left, text="🔍+",
                                           command=self._graph_zoom_in, width=3)
        self.graph_zoom_in_btn.pack(side=tk.LEFT, padx=1)

        self.graph_zoom_out_btn = ttk.Button(controls_left, text="🔍-",
                                            command=self._graph_zoom_out, width=3)
        self.graph_zoom_out_btn.pack(side=tk.LEFT, padx=1)

        self.graph_reset_btn = ttk.Button(controls_left, text="🔄",
                                         command=self._graph_reset_view, width=3)
        self.graph_reset_btn.pack(side=tk.LEFT, padx=1)

        self.graph_rearrange_btn = ttk.Button(controls_left, text="⚡",
                                             command=self._graph_rearrange, width=3)
        self.graph_rearrange_btn.pack(side=tk.LEFT, padx=1)

        # Right side controls
        controls_right = ttk.Frame(graph_controls_frame)
        controls_right.pack(side=tk.RIGHT)

        # Layout selector (compact)
        self.layout_var = tk.StringVar(value="spring")
        self.layout_combo = ttk.Combobox(controls_right, textvariable=self.layout_var,
                                        values=["spring", "circular", "shell", "kamada_kawai"],
                                        width=8, font=("Consolas", 7))
        self.layout_combo.pack(side=tk.RIGHT, padx=1)
        self.layout_combo.bind('<<ComboboxSelected>>', self._on_layout_change)

        ttk.Label(controls_right, text="Layout:", font=("Consolas", 7)).pack(side=tk.RIGHT, padx=(1, 2))

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

        # Note: Spatial relationships are now shown only in the graph view for clarity

        self.canvas_3d.draw()

    def _update_graph_view(self):
        """Update the network graph visualization."""
        self.ax_graph.clear()

        # Configure graph plot
        self.ax_graph.set_title('Directed Spatial Relationships')
        self.ax_graph.set_aspect('equal')
        self.ax_graph.axis('off')

        # Create NetworkX directed graph for spatial relationships
        G = nx.DiGraph()

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

        # Draw directed edges with arrows and curved paths
        import matplotlib.patches as patches

        for (a, b), label in edge_labels.items():
            if a in pos and b in pos:
                x1, y1 = pos[a]
                x2, y2 = pos[b]

                # Calculate arrow properties
                dx = x2 - x1
                dy = y2 - y1
                length = (dx**2 + dy**2)**0.5

                if length > 0:
                    # Normalize direction
                    dx_norm = dx / length
                    dy_norm = dy / length

                    # Offset start and end points to avoid overlapping with nodes
                    offset = 0.12
                    start_x = x1 + dx_norm * offset
                    start_y = y1 + dy_norm * offset
                    end_x = x2 - dx_norm * offset
                    end_y = y2 - dy_norm * offset

                    # Create curved path for better edge separation
                    curve_offset = 0.1
                    mid_x = (start_x + end_x) / 2 + dy_norm * curve_offset
                    mid_y = (start_y + end_y) / 2 - dx_norm * curve_offset

                    # Draw curved edge
                    self.ax_graph.plot([start_x, mid_x, end_x], [start_y, mid_y, end_y],
                                      'g-', alpha=0.7, linewidth=2, zorder=1)

                    # Draw arrowhead
                    arrow_size = 0.08
                    arrow = patches.FancyArrowPatch((mid_x, mid_y), (end_x, end_y),
                                                   arrowstyle='->', mutation_scale=15,
                                                   color='green', alpha=0.8, zorder=2)
                    self.ax_graph.add_patch(arrow)

                    # Add edge label (positioned along the curve)
                    label_x = mid_x
                    label_y = mid_y
                    self.ax_graph.text(label_x, label_y, label, ha='center', va='center',
                                      fontsize=7, color='darkgreen', zorder=3, weight='bold',
                                      bbox=dict(boxstyle="round,pad=0.2", facecolor='lightyellow',
                                               alpha=0.9, edgecolor='green'))

        # Set equal aspect and adjust limits with zoom support
        if pos:
            x_coords = [x for x, y in pos.values()]
            y_coords = [y for x, y in pos.values()]

            # Calculate base limits
            margin = 0.3
            base_xlim = (min(x_coords) - margin, max(x_coords) + margin)
            base_ylim = (min(y_coords) - margin, max(y_coords) + margin)

            # Apply zoom and custom limits (simple approach)
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
            self.start_btn.config(text="Stop Live Negotiation")
            self._log_activity("🚀 Starting live negotiation mode (continuous agent discussions)...")

            # Start simulation thread
            self.animation_thread = threading.Thread(target=self._simulation_loop)
            self.animation_thread.daemon = True
            self.animation_thread.start()
        else:
            self.running = False
            self.start_btn.config(text="Start Live Negotiation")
            self._log_activity("⏹️ Live negotiation stopped (relationships still update automatically on changes)")

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

            # Auto-update relationships after move
            self._auto_update_relationships_on_change()
            self._update_displays()  # Update again to show new relationships

            self._log_activity("📦 Moved chair to new position")

        except Exception as e:
            self._log_activity(f"❌ Move error: {str(e)}")

    def _reset_scene(self):
        """Reset the scene to initial state."""
        try:
            # Stop simulation
            self.running = False
            self.start_btn.config(text="Start Live Negotiation")

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

        # Clear LLM conversation history as well
        if hasattr(self.command_parser, 'llm_client') and self.command_parser.llm_client:
            self.command_parser.llm_client.conversation_history.clear()

        self._add_chat_message("system", "Chat cleared. Ready for new commands!")
        self._log_activity("🧹 Chat and conversation context cleared")

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

            # Add to conversation history for context
            if hasattr(self.command_parser, 'llm_client') and self.command_parser.llm_client:
                self.command_parser.llm_client.add_to_conversation_history(
                    command=command_text,
                    result=parsed_command.__dict__ if parsed_command else {},
                    success=success
                )

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

            # Sync agents from scene modifier (in case new objects were added)
            self.agents.update(self.scene_modifier.agents)

            # Log support system status if objects were added/removed
            if hasattr(parsed_command, 'action') and parsed_command.action in ['add', 'remove']:
                support_status = self.scene_modifier.support_system.get_system_status()
                scene_info = support_status['scene_analysis']
                self._log_activity(f"📊 Scene: {scene_info['total_objects']} objects, {scene_info['supported_objects']} supported, {scene_info['ground_objects']} on ground")

            # Auto-update relationships after scene modification
            self._auto_update_relationships_on_change()

            # Update displays again to show new relationships
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

    def _auto_calculate_relationships(self):
        """Automatically calculate spatial relationships for all objects with visible negotiation."""
        try:
            self._log_activity("🤝 Starting agent negotiations for spatial relationships...")
            initial_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])

            # Run agent simulation with detailed logging
            for i in range(5):  # 5 ticks should be enough for initial discovery
                self._log_activity(f"   🔄 Negotiation round {i+1}/5...")

                # Track messages before tick
                initial_msgs = sum(len(self.bus.queues[aid]) for aid in self.agents.keys())

                tick(self.graph, self.bus, self.agents)

                # Track messages after tick and log activity
                final_msgs = sum(len(self.bus.queues[aid]) for aid in self.agents.keys())
                current_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])

                if current_relations > initial_relations:
                    new_relations = current_relations - initial_relations
                    self._log_activity(f"   ✨ Found {new_relations} new relationships")
                    initial_relations = current_relations

                # Update display after each significant tick
                if i % 2 == 1:  # Update every other tick to show progress
                    self._update_displays()

            # Final count
            final_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])
            total_discovered = final_relations - (initial_relations - (final_relations - initial_relations))

            if total_discovered > 0:
                self._log_activity(f"🎉 Agent negotiations complete! Established {final_relations} spatial relationships")
            else:
                self._log_activity("ℹ️ No spatial relationships detected in current scene")

        except Exception as e:
            self._log_activity(f"❌ Negotiation error: {str(e)}")

    def _auto_update_relationships_on_change(self):
        """Run visible agent negotiations when the scene changes."""
        try:
            self._log_activity("🔍 Scene changed - agents analyzing new spatial relationships...")
            initial_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])

            # Run 3-5 ticks with visible progress
            for i in range(4):
                self._log_activity(f"   🤝 Agents negotiating... (round {i+1})")
                tick(self.graph, self.bus, self.agents)

                # Check for new relationships
                current_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])
                if current_relations > initial_relations:
                    new_count = current_relations - initial_relations
                    self._log_activity(f"   ✅ {new_count} new spatial relationship(s) established")
                    initial_relations = current_relations

            # Final summary
            final_relations = len([r for r in self.graph.relations.keys() if r[0] != "in"])
            if final_relations != initial_relations:
                self._log_activity("🎯 Spatial context updated successfully")
            else:
                self._log_activity("ℹ️ No new relationships detected")

        except Exception as e:
            self._log_activity(f"❌ Spatial analysis error: {str(e)}")


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

        # Auto-calculate initial spatial relationships
        self._log_activity("🧠 Initializing intrinsic spatial context...")
        self._auto_calculate_relationships()

        self._update_displays()
        self.root.mainloop()

    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'running'):
            self.running = False
