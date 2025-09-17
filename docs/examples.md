# SpacXT Examples

## 🎯 Basic Examples

### Hello SpacXT

The simplest possible SpacXT application:

```python
import json
from spacxt import SceneGraph, Bus, make_agents, tick

# Minimal scene with two objects
scene_data = {
    "scene": {
        "id": "hello_world",
        "objects": [
            {
                "id": "box_a",
                "cls": "box",
                "pos": [0.0, 0.0, 0.0],
                "ori": [0, 0, 0, 1],
                "bbox": {"type": "OBB", "xyz": [0.5, 0.5, 0.5]},
                "conf": 1.0
            },
            {
                "id": "box_b",
                "cls": "box",
                "pos": [0.5, 0.0, 0.0],
                "ori": [0, 0, 0, 1],
                "bbox": {"type": "OBB", "xyz": [0.5, 0.5, 0.5]},
                "conf": 1.0
            }
        ],
        "relations": []
    }
}

# Initialize SpacXT
graph = SceneGraph()
graph.load_bootstrap(scene_data)

bus = Bus()
agents = make_agents(graph, bus, ["box_a", "box_b"])

# Run simulation
print("Running spatial reasoning...")
for i in range(5):
    tick(graph, bus, agents)

# Show discovered relationships
print("\\nDiscovered relationships:")
for (r, a, b), rel in graph.relations.items():
    print(f"  {a} {r} {b} (confidence: {rel.conf:.2f})")
```

### Custom Scene Builder

Build scenes programmatically:

```python
from spacxt import SceneGraph, Node, Relation

def create_office_scene():
    """Create a simple office scene."""

    # Create scene graph
    graph = SceneGraph()

    # Add desk
    desk = Node(
        id="desk_1",
        cls="desk",
        pos=(2.0, 1.0, 0.75),
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [1.5, 0.8, 0.75]},
        aff=["support", "work_surface"],
        lom="fixed",
        conf=0.95
    )
    graph.nodes["desk_1"] = desk

    # Add chair
    chair = Node(
        id="chair_1",
        cls="chair",
        pos=(2.0, 0.3, 0.45),
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.6, 0.6, 0.9]},
        aff=["sit"],
        lom="medium",
        conf=0.92
    )
    graph.nodes["chair_1"] = chair

    # Add monitor
    monitor = Node(
        id="monitor_1",
        cls="monitor",
        pos=(2.0, 1.4, 1.1),
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.6, 0.05, 0.4]},
        aff=["display"],
        lom="fixed",
        conf=0.98,
        state={"power": "on", "brightness": 80}
    )
    graph.nodes["monitor_1"] = monitor

    # Add initial relationships
    on_rel = Relation(
        r="on",
        a="monitor_1",
        b="desk_1",
        conf=0.99,
        props={"support_type": "direct"}
    )
    graph.relations[("on", "monitor_1", "desk_1")] = on_rel

    return graph

# Use the scene
office = create_office_scene()
bus = Bus()
agents = make_agents(office, bus, ["desk_1", "chair_1", "monitor_1"])

# Run simulation
for i in range(10):
    tick(office, bus, agents)

print("Office spatial relationships:")
for (r, a, b), rel in office.relations.items():
    print(f"  {a} {r} {b} (conf: {rel.conf:.2f})")
```

## 🛠️ Advanced Examples

### Custom Spatial Reasoning Tool

Implement domain-specific spatial relationships:

```python
from spacxt.tools.topo_tool import dist

def relate_aligned(node_a, node_b, alignment_thresh=0.1):
    """Check if two objects are aligned along an axis."""
    pos_a = node_a["pos"]
    pos_b = node_b["pos"]

    # Check X-axis alignment
    x_diff = abs(pos_a[0] - pos_b[0])
    y_diff = abs(pos_a[1] - pos_b[1])
    z_diff = abs(pos_a[2] - pos_b[2])

    alignments = []
    if x_diff < alignment_thresh:
        alignments.append("x_aligned")
    if y_diff < alignment_thresh:
        alignments.append("y_aligned")
    if z_diff < alignment_thresh:
        alignments.append("z_aligned")

    if alignments:
        # Calculate confidence based on how well aligned
        best_alignment = min(x_diff, y_diff, z_diff)
        conf = max(0.1, 1.0 - (best_alignment / alignment_thresh))

        return {
            "r": "aligned",
            "a": node_a["id"],
            "b": node_b["id"],
            "conf": conf,
            "props": {
                "alignments": alignments,
                "best_alignment_error": best_alignment
            }
        }
    else:
        return {
            "r": "misaligned",
            "a": node_a["id"],
            "b": node_b["id"],
            "conf": 0.8,
            "props": {"min_error": min(x_diff, y_diff, z_diff)}
        }

# Custom agent that uses alignment reasoning
class AlignmentAgent(Agent):
    def perceive_and_propose(self):
        # Standard spatial reasoning
        super().perceive_and_propose()

        # Add alignment reasoning
        me = self.graph.get_node(self.id)
        if not me:
            return

        neighbors = self.graph.neighbors(self.id, radius=3.0)

        for nb in neighbors:
            rel = relate_aligned(me.__dict__, nb.__dict__)

            if rel["r"] == "aligned" and rel["conf"] > 0.6:
                msg = A2AMessage(
                    type="RELATION_PROPOSE",
                    sender=self.id,
                    receiver=nb.id,
                    payload={
                        "relation": rel,
                        "basis": "custom.relate_aligned"
                    }
                )
                self.send(msg)

# Use custom agent
def create_agents_with_alignment(graph, bus, ids):
    agents = {}
    for nid in ids:
        node = graph.get_node(nid)
        if not node:
            continue
        agent = AlignmentAgent(
            id=nid,
            cls=node.cls,
            graph=graph,
            send=bus.send,
            inbox=[]
        )
        agents[nid] = agent
    return agents
```

### Multi-Room Environment

Complex scene with multiple rooms and spatial zones:

```python
def create_apartment_scene():
    """Create a multi-room apartment scene."""

    apartment_data = {
        "scene": {
            "id": "apartment_101",
            "frame": "map",
            "rooms": [
                {
                    "id": "living_room",
                    "bbox": {"min": [0, 0, 0], "max": [5, 4, 3]}
                },
                {
                    "id": "kitchen",
                    "bbox": {"min": [5, 0, 0], "max": [8, 4, 3]}
                },
                {
                    "id": "bedroom",
                    "bbox": {"min": [0, 4, 0], "max": [5, 7, 3]}
                }
            ],
            "objects": [
                # Living room furniture
                {
                    "id": "sofa_1",
                    "cls": "sofa",
                    "pos": [2.5, 1.0, 0.4],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [2.0, 0.8, 0.8]},
                    "aff": ["sit", "lie_down"],
                    "lom": "medium",
                    "conf": 0.95
                },
                {
                    "id": "tv_1",
                    "cls": "television",
                    "pos": [2.5, 3.5, 1.2],
                    "ori": [0, 0, 1, 0],  # Rotated 180 degrees
                    "bbox": {"type": "OBB", "xyz": [1.2, 0.1, 0.7]},
                    "aff": ["display", "entertainment"],
                    "lom": "fixed",
                    "conf": 0.98,
                    "state": {"power": "off", "channel": 1}
                },
                {
                    "id": "coffee_table_1",
                    "cls": "table",
                    "pos": [2.5, 2.0, 0.4],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [1.2, 0.6, 0.4]},
                    "aff": ["support"],
                    "lom": "medium",
                    "conf": 0.90
                },

                # Kitchen appliances
                {
                    "id": "refrigerator_1",
                    "cls": "refrigerator",
                    "pos": [7.5, 0.5, 0.9],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.6, 0.6, 1.8]},
                    "aff": ["storage", "cooling"],
                    "lom": "fixed",
                    "conf": 0.99,
                    "state": {"temperature": 4, "power": "on"}
                },
                {
                    "id": "stove_1",
                    "cls": "stove",
                    "pos": [6.0, 3.5, 0.9],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.6, 0.6, 0.9]},
                    "aff": ["cooking", "heat"],
                    "lom": "fixed",
                    "conf": 0.95,
                    "state": {"power": "off", "temperature": 20}
                },
                {
                    "id": "kitchen_counter_1",
                    "cls": "counter",
                    "pos": [6.5, 2.0, 0.9],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [2.5, 0.6, 0.9]},
                    "aff": ["support", "work_surface"],
                    "lom": "fixed",
                    "conf": 0.98
                },

                # Bedroom furniture
                {
                    "id": "bed_1",
                    "cls": "bed",
                    "pos": [2.5, 6.0, 0.5],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [2.0, 1.5, 1.0]},
                    "aff": ["sleep", "lie_down"],
                    "lom": "fixed",
                    "conf": 0.95
                },
                {
                    "id": "nightstand_1",
                    "cls": "nightstand",
                    "pos": [1.0, 6.0, 0.6],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.4, 0.4, 0.6]},
                    "aff": ["storage", "support"],
                    "lom": "medium",
                    "conf": 0.88
                }
            ],
            "relations": [
                # Room containment relationships
                {"r": "in", "a": "sofa_1", "b": "living_room"},
                {"r": "in", "a": "tv_1", "b": "living_room"},
                {"r": "in", "a": "coffee_table_1", "b": "living_room"},
                {"r": "in", "a": "refrigerator_1", "b": "kitchen"},
                {"r": "in", "a": "stove_1", "b": "kitchen"},
                {"r": "in", "a": "kitchen_counter_1", "b": "kitchen"},
                {"r": "in", "a": "bed_1", "b": "bedroom"},
                {"r": "in", "a": "nightstand_1", "b": "bedroom"},

                # Functional relationships
                {"r": "faces", "a": "sofa_1", "b": "tv_1"},
                {"r": "adjacent_to", "a": "nightstand_1", "b": "bed_1"}
            ]
        }
    }

    return apartment_data

# Load and simulate apartment
apartment_data = create_apartment_scene()
graph = SceneGraph()
graph.load_bootstrap(apartment_data)

bus = Bus()
agent_ids = [obj["id"] for obj in apartment_data["scene"]["objects"]]
agents = make_agents(graph, bus, agent_ids)

print(f"Simulating apartment with {len(agents)} agents...")

# Run extended simulation
for i in range(20):
    tick(graph, bus, agents)

    if i % 5 == 0:
        discovered = [r for r in graph.relations.keys() if r[0] not in ["in", "faces", "adjacent_to"]]
        print(f"  Tick {i}: {len(discovered)} new relationships discovered")

# Analyze results by room
print("\\nSpatial relationships by room:")

rooms = ["living_room", "kitchen", "bedroom"]
for room in rooms:
    print(f"\\n{room.upper()}:")
    room_objects = [obj["id"] for obj in apartment_data["scene"]["objects"]
                   if any(rel["r"] == "in" and rel["a"] == obj["id"] and rel["b"] == room
                         for rel in apartment_data["scene"]["relations"])]

    for (r, a, b), rel in graph.relations.items():
        if a in room_objects and b in room_objects and r not in ["in"]:
            print(f"  {a} {r} {b} (conf: {rel.conf:.2f})")
```

### Dynamic Scene Modification

Demonstrate real-time scene updates:

```python
import time
from spacxt import GraphPatch

def simulate_moving_robot():
    """Simulate a robot moving through a scene."""

    # Create simple scene
    scene_data = {
        "scene": {
            "id": "robot_demo",
            "objects": [
                {
                    "id": "robot_1",
                    "cls": "robot",
                    "pos": [0.0, 0.0, 0.3],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.4, 0.4, 0.6]},
                    "aff": ["mobile"],
                    "lom": "high",
                    "conf": 1.0,
                    "state": {"battery": 85, "status": "moving"}
                },
                {
                    "id": "obstacle_1",
                    "cls": "box",
                    "pos": [2.0, 0.0, 0.3],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.5, 0.5, 0.6]},
                    "lom": "fixed",
                    "conf": 0.95
                },
                {
                    "id": "goal_1",
                    "cls": "target",
                    "pos": [4.0, 0.0, 0.1],
                    "ori": [0, 0, 0, 1],
                    "bbox": {"type": "OBB", "xyz": [0.3, 0.3, 0.2]},
                    "lom": "fixed",
                    "conf": 0.90
                }
            ],
            "relations": []
        }
    }

    # Initialize scene
    graph = SceneGraph()
    graph.load_bootstrap(scene_data)

    bus = Bus()
    agents = make_agents(graph, bus, ["robot_1", "obstacle_1", "goal_1"])

    # Robot path
    waypoints = [
        (0.5, 0.0, 0.3),
        (1.0, 0.0, 0.3),
        (1.5, 0.5, 0.3),  # Avoid obstacle
        (2.5, 0.5, 0.3),
        (3.0, 0.0, 0.3),
        (3.5, 0.0, 0.3),
        (4.0, 0.0, 0.3)   # Reach goal
    ]

    print("Robot navigation simulation:")
    print("=" * 40)

    for i, waypoint in enumerate(waypoints):
        print(f"\\nStep {i+1}: Moving robot to {waypoint}")

        # Update robot position
        patch = GraphPatch()
        patch.update_nodes["robot_1"] = {
            "pos": waypoint,
            "state": {"battery": 85 - i*2, "status": "moving"}
        }
        graph.apply_patch(patch)

        # Run spatial reasoning
        for _ in range(3):
            tick(graph, bus, agents)

        # Show current spatial relationships
        robot_relations = []
        for (r, a, b), rel in graph.relations.items():
            if "robot_1" in [a, b]:
                robot_relations.append((r, a, b, rel.conf))

        if robot_relations:
            print("  Current relationships:")
            for r, a, b, conf in robot_relations:
                print(f"    {a} {r} {b} (conf: {conf:.2f})")
        else:
            print("  No relationships detected")

        # Check if goal reached
        robot_pos = graph.get_node("robot_1").pos
        goal_pos = graph.get_node("goal_1").pos
        distance_to_goal = ((robot_pos[0] - goal_pos[0])**2 +
                           (robot_pos[1] - goal_pos[1])**2 +
                           (robot_pos[2] - goal_pos[2])**2)**0.5

        if distance_to_goal < 0.5:
            print("  🎯 GOAL REACHED!")

            # Update robot status
            patch = GraphPatch()
            patch.update_nodes["robot_1"] = {"state": {"status": "arrived"}}
            graph.apply_patch(patch)
            break

        time.sleep(0.5)  # Simulate time passage

# Run the simulation
simulate_moving_robot()
```

### Learning Agent

Agent that adapts its behavior based on experience:

```python
import random
from collections import defaultdict

class LearningAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.relationship_history = defaultdict(list)
        self.success_rates = defaultdict(float)
        self.learning_rate = 0.1

    def perceive_and_propose(self):
        """Enhanced perception with learning."""
        me = self.graph.get_node(self.id)
        if not me:
            return []

        neighbors = self.graph.neighbors(self.id, radius=1.5)
        msgs = []

        for nb in neighbors:
            # Standard spatial evaluation
            rel = relate_near(me.__dict__, nb.__dict__)

            # Apply learning: adjust confidence based on historical success
            relationship_key = (self.id, nb.id, rel["r"])
            if relationship_key in self.success_rates:
                # Blend original confidence with learned success rate
                learned_conf = self.success_rates[relationship_key]
                original_conf = rel["conf"]
                rel["conf"] = (1 - self.learning_rate) * original_conf + self.learning_rate * learned_conf

            # Propose if confidence is sufficient
            if rel["r"] == "near" and rel["conf"] > 0.5:  # Lower threshold for learning
                msg = A2AMessage(
                    type="RELATION_PROPOSE",
                    sender=self.id,
                    receiver=nb.id,
                    payload={
                        "relation": rel,
                        "basis": "learning.relate_near",
                        "original_conf": rel["conf"]
                    }
                )
                self.send(msg)
                msgs.append(msg)

        return msgs

    def handle_inbox(self):
        """Enhanced message handling with learning."""
        patch = GraphPatch()

        while self.inbox:
            msg = self.inbox.pop(0)

            if msg.type == "RELATION_PROPOSE" and msg.receiver == self.id:
                rel = msg.payload["relation"]
                relationship_key = (msg.sender, self.id, rel["r"])

                # Decision based on confidence
                decision = "accept" if rel.get("conf", 0) >= 0.6 else "reject"

                # Send acknowledgment
                ack = A2AMessage(
                    type="RELATION_ACK",
                    sender=self.id,
                    receiver=msg.sender,
                    payload={"relation": rel, "decision": decision}
                )
                self.send(ack)

                # Learn from decision
                self.relationship_history[relationship_key].append({
                    "confidence": rel.get("conf", 0),
                    "decision": decision,
                    "timestamp": time.time()
                })

                # Add to graph if accepted
                if decision == "accept":
                    r = Relation(
                        r=rel["r"],
                        a=rel["a"],
                        b=rel["b"],
                        props=rel.get("props", {}),
                        conf=rel.get("conf", 1.0)
                    )
                    patch.add_relations.append(r)

            elif msg.type == "RELATION_ACK" and msg.receiver == self.id:
                # Learn from acknowledgment
                rel = msg.payload["relation"]
                decision = msg.payload["decision"]
                relationship_key = (self.id, msg.sender, rel["r"])

                # Update success rate
                self.update_success_rate(relationship_key, decision == "accept")

        return patch

    def update_success_rate(self, relationship_key, success):
        """Update learned success rate for a relationship type."""
        current_rate = self.success_rates.get(relationship_key, 0.5)

        if success:
            new_rate = current_rate + self.learning_rate * (1.0 - current_rate)
        else:
            new_rate = current_rate + self.learning_rate * (0.0 - current_rate)

        self.success_rates[relationship_key] = max(0.1, min(0.9, new_rate))

    def get_learning_stats(self):
        """Get learning statistics."""
        stats = {
            "total_relationships_tried": len(self.relationship_history),
            "success_rates": dict(self.success_rates),
            "recent_history": {}
        }

        # Get recent history for each relationship type
        for key, history in self.relationship_history.items():
            if len(history) >= 3:  # Only if we have enough data
                recent = history[-3:]
                success_count = sum(1 for h in recent if h["decision"] == "accept")
                stats["recent_history"][key] = {
                    "attempts": len(recent),
                    "successes": success_count,
                    "rate": success_count / len(recent)
                }

        return stats

# Demo learning behavior
def demo_learning():
    """Demonstrate learning agent behavior."""

    # Create scene with objects that will move around
    scene_data = {
        "scene": {
            "id": "learning_demo",
            "objects": [
                {"id": "learner_1", "cls": "agent", "pos": [1.0, 1.0, 0.5],
                 "ori": [0,0,0,1], "bbox": {"type": "OBB", "xyz": [0.3,0.3,0.3]}, "conf": 1.0},
                {"id": "target_1", "cls": "target", "pos": [1.5, 1.0, 0.5],
                 "ori": [0,0,0,1], "bbox": {"type": "OBB", "xyz": [0.3,0.3,0.3]}, "conf": 1.0},
                {"id": "target_2", "cls": "target", "pos": [2.0, 1.0, 0.5],
                 "ori": [0,0,0,1], "bbox": {"type": "OBB", "xyz": [0.3,0.3,0.3]}, "conf": 1.0}
            ],
            "relations": []
        }
    }

    # Initialize with learning agent
    graph = SceneGraph()
    graph.load_bootstrap(scene_data)

    bus = Bus()

    # Create learning agent
    learning_agent = LearningAgent(
        id="learner_1",
        cls="agent",
        graph=graph,
        send=bus.send,
        inbox=[]
    )

    # Regular agents for targets
    regular_agents = make_agents(graph, bus, ["target_1", "target_2"])
    agents = {"learner_1": learning_agent, **regular_agents}

    print("Learning Agent Demo")
    print("=" * 30)

    # Run multiple episodes with position changes
    for episode in range(5):
        print(f"\\nEpisode {episode + 1}:")

        # Randomly move targets
        new_pos_1 = (1.0 + random.uniform(-0.5, 0.5), 1.0 + random.uniform(-0.5, 0.5), 0.5)
        new_pos_2 = (2.0 + random.uniform(-0.5, 0.5), 1.0 + random.uniform(-0.5, 0.5), 0.5)

        patch = GraphPatch()
        patch.update_nodes["target_1"] = {"pos": new_pos_1}
        patch.update_nodes["target_2"] = {"pos": new_pos_2}
        graph.apply_patch(patch)

        # Run simulation
        for i in range(10):
            tick(graph, bus, agents)

        # Show learning progress
        stats = learning_agent.get_learning_stats()
        print(f"  Relationships attempted: {stats['total_relationships_tried']}")

        if stats['success_rates']:
            print("  Success rates:")
            for key, rate in stats['success_rates'].items():
                print(f"    {key}: {rate:.2f}")

# Run learning demo
demo_learning()
```

## 🎨 Visualization Examples

### Custom 3D Renderer

Create custom visualization for specific domains:

```python
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class CustomSceneRenderer:
    def __init__(self, scene_graph):
        self.graph = scene_graph
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')

    def render_warehouse_scene(self):
        """Specialized rendering for warehouse environments."""
        self.ax.clear()

        # Color scheme for warehouse objects
        colors = {
            'shelf': 'brown',
            'robot': 'blue',
            'package': 'orange',
            'conveyor': 'gray',
            'workstation': 'green'
        }

        # Render objects with warehouse-specific styling
        for node_id, node in self.graph.nodes.items():
            color = colors.get(node.cls, 'red')

            # Special rendering for different object types
            if node.cls == 'shelf':
                self._draw_shelf(node, color)
            elif node.cls == 'robot':
                self._draw_robot(node, color)
            elif node.cls == 'conveyor':
                self._draw_conveyor(node, color)
            else:
                self._draw_box(node.pos, node.bbox['xyz'], color)

            # Add labels with warehouse info
            self._add_warehouse_label(node)

        # Render relationships with warehouse semantics
        self._render_warehouse_relationships()

        # Configure warehouse-appropriate view
        self.ax.set_xlabel('X (meters)')
        self.ax.set_ylabel('Y (meters)')
        self.ax.set_zlabel('Height (meters)')
        self.ax.set_title('Warehouse Spatial Intelligence')

        plt.tight_layout()
        plt.show()

    def _draw_shelf(self, node, color):
        """Draw a warehouse shelf with multiple levels."""
        pos = node.pos
        size = node.bbox['xyz']

        # Draw shelf structure
        levels = 4
        level_height = size[2] / levels

        for level in range(levels):
            z_offset = level * level_height
            level_pos = (pos[0], pos[1], pos[2] + z_offset)
            level_size = (size[0], size[1], level_height * 0.1)  # Thin shelves
            self._draw_box(level_pos, level_size, color, alpha=0.6)

    def _draw_robot(self, node, color):
        """Draw a mobile robot with direction indicator."""
        pos = node.pos
        size = node.bbox['xyz']

        # Main body
        self._draw_box(pos, size, color, alpha=0.8)

        # Direction indicator (simple arrow)
        arrow_start = np.array(pos)
        arrow_end = arrow_start + np.array([size[0]/2, 0, 0])

        self.ax.plot([arrow_start[0], arrow_end[0]],
                    [arrow_start[1], arrow_end[1]],
                    [arrow_start[2], arrow_end[2]],
                    'r-', linewidth=3)

    def _draw_conveyor(self, node, color):
        """Draw a conveyor belt system."""
        pos = node.pos
        size = node.bbox['xyz']

        # Main conveyor body
        self._draw_box(pos, size, color, alpha=0.7)

        # Conveyor surface pattern
        segments = 10
        for i in range(segments):
            x_offset = (i / segments - 0.5) * size[0]
            line_pos = (pos[0] + x_offset, pos[1], pos[2] + size[2]/2)

            self.ax.plot([line_pos[0], line_pos[0]],
                        [line_pos[1] - size[1]/2, line_pos[1] + size[1]/2],
                        [line_pos[2], line_pos[2]],
                        'k-', alpha=0.3)

    def _draw_box(self, center, size, color, alpha=0.7):
        """Draw a 3D box."""
        x, y, z = center
        dx, dy, dz = size

        # Define box vertices
        vertices = [
            [x-dx/2, y-dy/2, z-dz/2], [x+dx/2, y-dy/2, z-dz/2],
            [x+dx/2, y+dy/2, z-dz/2], [x-dx/2, y+dy/2, z-dz/2],
            [x-dx/2, y-dy/2, z+dz/2], [x+dx/2, y-dy/2, z+dz/2],
            [x+dx/2, y+dy/2, z+dz/2], [x-dx/2, y+dy/2, z+dz/2]
        ]

        # Define box faces
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[2], vertices[3], vertices[7], vertices[6]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]]
        ]

        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        collection = Poly3DCollection(faces, facecolors=color, alpha=alpha, edgecolors='black')
        self.ax.add_collection3d(collection)

    def _add_warehouse_label(self, node):
        """Add warehouse-specific labels."""
        pos = node.pos
        size = node.bbox['xyz']

        # Position label above object
        label_pos = (pos[0], pos[1], pos[2] + size[2]/2 + 0.1)

        # Warehouse-specific label content
        if node.cls == 'robot':
            battery = node.state.get('battery', 'Unknown')
            status = node.state.get('status', 'idle')
            label = f"{node.id}\\n{status}\\n{battery}%"
        elif node.cls == 'shelf':
            capacity = node.state.get('capacity', 'Unknown')
            occupancy = node.state.get('occupancy', 0)
            label = f"{node.id}\\n{occupancy}/{capacity}"
        else:
            label = f"{node.id}\\n({node.cls})"

        self.ax.text(label_pos[0], label_pos[1], label_pos[2],
                    label, fontsize=8, ha='center')

    def _render_warehouse_relationships(self):
        """Render relationships with warehouse semantics."""
        for (rel_type, a, b), relation in self.graph.relations.items():
            if a not in self.graph.nodes or b not in self.graph.nodes:
                continue

            node_a = self.graph.nodes[a]
            node_b = self.graph.nodes[b]

            # Skip containment relationships for cleaner view
            if rel_type in ['in', 'contains']:
                continue

            # Warehouse-specific relationship rendering
            if rel_type == 'near':
                line_color = 'green'
                line_style = '-'
                line_width = 2
            elif rel_type == 'blocks':
                line_color = 'red'
                line_style = '--'
                line_width = 3
            elif rel_type == 'serves':
                line_color = 'blue'
                line_style = '-.'
                line_width = 2
            else:
                line_color = 'gray'
                line_style = '-'
                line_width = 1

            # Draw relationship line
            self.ax.plot([node_a.pos[0], node_b.pos[0]],
                        [node_a.pos[1], node_b.pos[1]],
                        [node_a.pos[2], node_b.pos[2]],
                        color=line_color, linestyle=line_style,
                        linewidth=line_width, alpha=0.7)

            # Add relationship label
            mid_pos = [(node_a.pos[i] + node_b.pos[i])/2 for i in range(3)]
            self.ax.text(mid_pos[0], mid_pos[1], mid_pos[2],
                        f"{rel_type}\\n{relation.conf:.2f}",
                        fontsize=6, ha='center',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

# Example usage
def visualize_warehouse():
    """Create and visualize a warehouse scene."""

    warehouse_data = {
        "scene": {
            "id": "warehouse_floor_1",
            "objects": [
                {
                    "id": "shelf_A1", "cls": "shelf",
                    "pos": [2.0, 1.0, 1.5], "ori": [0,0,0,1],
                    "bbox": {"type": "OBB", "xyz": [1.0, 0.3, 3.0]},
                    "state": {"capacity": 100, "occupancy": 75}
                },
                {
                    "id": "robot_R1", "cls": "robot",
                    "pos": [0.5, 1.0, 0.3], "ori": [0,0,0,1],
                    "bbox": {"type": "OBB", "xyz": [0.6, 0.4, 0.6]},
                    "state": {"battery": 85, "status": "picking"}
                },
                {
                    "id": "conveyor_C1", "cls": "conveyor",
                    "pos": [4.0, 2.0, 0.5], "ori": [0,0,0,1],
                    "bbox": {"type": "OBB", "xyz": [3.0, 0.5, 1.0]},
                    "state": {"speed": 1.2, "direction": "east"}
                }
            ],
            "relations": []
        }
    }

    # Create and simulate scene
    graph = SceneGraph()
    graph.load_bootstrap(warehouse_data)

    bus = Bus()
    agents = make_agents(graph, bus, ["shelf_A1", "robot_R1", "conveyor_C1"])

    # Run simulation
    for i in range(15):
        tick(graph, bus, agents)

    # Render with custom renderer
    renderer = CustomSceneRenderer(graph)
    renderer.render_warehouse_scene()

# Run warehouse visualization
# visualize_warehouse()
```

---

*These examples demonstrate the flexibility and power of SpacXT for various spatial reasoning applications. Use them as starting points for your own spatial intelligence systems!*
