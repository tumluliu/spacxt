# SpacXT API Reference

## 📦 Core Classes

### SceneGraph

The central data structure that maintains spatial state and relationships.

```python
from spacxt import SceneGraph

graph = SceneGraph()
```

#### Methods

##### `load_bootstrap(data: Dict[str, Any]) -> None`
Initialize the scene from bootstrap configuration.

```python
with open("scene.json", "r") as f:
    data = json.load(f)
graph.load_bootstrap(data)
```

##### `get_node(node_id: str) -> Optional[Node]`
Retrieve a node by ID.

```python
table = graph.get_node("table_1")
if table:
    print(f"Table position: {table.pos}")
```

##### `neighbors(node_id: str, radius: float = 1.5) -> List[Node]`
Find all nodes within radius of the specified node.

```python
nearby = graph.neighbors("chair_12", radius=2.0)
print(f"Found {len(nearby)} nearby objects")
```

##### `apply_patch(patch: GraphPatch) -> None`
Apply changes to the scene graph.

```python
patch = GraphPatch()
patch.update_nodes["chair_12"] = {"pos": (2.0, 1.5, 0.45)}
graph.apply_patch(patch)
```

##### `as_llm_context(agent_pose: Tuple, roi: str, K: int = 6) -> Dict`
Generate LLM-ready spatial context.

```python
context = graph.as_llm_context(
    agent_pose=(2.7, 1.3, 1.6),
    roi="kitchen",
    K=5
)
```

#### Properties

- `nodes: Dict[str, Node]` - All objects in the scene
- `relations: Dict[Tuple[str,str,str], Relation]` - Spatial relationships
- `events: List[Dict[str,Any]]` - Change history

---

### Node

Represents an object in the 3D scene.

```python
from spacxt import Node

node = Node(
    id="table_1",
    cls="table",
    pos=(1.5, 1.5, 0.75),
    ori=(0, 0, 0, 1),
    bbox={"type": "OBB", "xyz": [1.2, 0.8, 0.75]},
    conf=0.98
)
```

#### Fields

- `id: str` - Unique identifier
- `cls: str` - Object class/type
- `pos: Tuple[float, float, float]` - 3D position
- `ori: Tuple[float, float, float, float]` - Quaternion orientation
- `bbox: Dict[str, Any]` - Bounding box definition
- `aff: List[str]` - Affordances (e.g., ["sit", "support"])
- `lom: str` - Level of mobility ("fixed", "medium", "high")
- `conf: float` - Confidence score (0.0-1.0)
- `state: Dict[str, Any]` - Dynamic state properties
- `meta: Dict[str, Any]` - Additional metadata

---

### Relation

Represents a spatial relationship between two objects.

```python
from spacxt import Relation

rel = Relation(
    r="near",
    a="chair_12",
    b="table_1",
    props={"dist": 0.68},
    conf=0.85
)
```

#### Fields

- `r: str` - Relationship type ("near", "far", "in", etc.)
- `a: str` - Source object ID
- `b: str` - Target object ID
- `props: Dict[str, Any]` - Relationship properties
- `ts: float` - Timestamp
- `conf: float` - Confidence score (0.0-1.0)

---

### Agent

Autonomous agent that reasons about spatial relationships.

```python
from spacxt import Agent

agent = Agent(
    id="table_1",
    cls="table",
    graph=scene_graph,
    send=message_bus.send,
    inbox=[]
)
```

#### Methods

##### `perceive_and_propose() -> List[A2AMessage]`
Scan environment and propose relationships to neighbors.

```python
messages = agent.perceive_and_propose()
print(f"Agent sent {len(messages)} proposals")
```

##### `handle_inbox() -> GraphPatch`
Process incoming messages and generate scene updates.

```python
patch = agent.handle_inbox()
if patch.add_relations:
    scene_graph.apply_patch(patch)
```

#### Fields

- `id: str` - Agent identifier (matches node ID)
- `cls: str` - Object class
- `graph: SceneGraph` - Reference to scene graph
- `send: Callable` - Message sending function
- `inbox: List[A2AMessage]` - Incoming messages

---

### GraphPatch

CRDT-style update for scene graph modifications.

```python
from spacxt import GraphPatch

patch = GraphPatch()
patch.update_nodes["chair_12"] = {"pos": (2.0, 1.5, 0.45)}
patch.add_relations.append(
    Relation(r="near", a="chair_12", b="stove", conf=0.75)
)
```

#### Fields

- `add_nodes: Dict[str, Node]` - Nodes to add
- `update_nodes: Dict[str, Dict[str, Any]]` - Node property updates
- `add_relations: List[Relation]` - Relations to add
- `remove_relations: List[Tuple[str,str,str]]` - Relations to remove

---

### A2AMessage

Agent-to-agent communication message.

```python
from spacxt import A2AMessage

msg = A2AMessage(
    type="RELATION_PROPOSE",
    sender="chair_12",
    receiver="table_1",
    payload={
        "relation": {"r": "near", "conf": 0.85},
        "basis": "topo.relate_near"
    }
)
```

#### Fields

- `type: str` - Message type ("RELATION_PROPOSE", "RELATION_ACK")
- `sender: str` - Sending agent ID
- `receiver: str` - Target agent ID
- `payload: Dict[str, Any]` - Message content
- `ts: float` - Timestamp

---

## 🔧 Orchestration

### Bus

Message bus for agent communication.

```python
from spacxt import Bus

bus = Bus()
bus.send(message)
messages = bus.drain("agent_id")
```

#### Methods

##### `send(msg: A2AMessage) -> None`
Send message to target agent.

##### `drain(agent_id: str) -> List[A2AMessage]`
Retrieve and clear messages for agent.

---

### Orchestration Functions

##### `make_agents(graph: SceneGraph, bus: Bus, ids: List[str]) -> Dict[str, Agent]`
Create agents for specified node IDs.

```python
from spacxt import make_agents

agents = make_agents(graph, bus, ["table_1", "chair_12", "stove"])
```

##### `tick(graph: SceneGraph, bus: Bus, agents: Dict[str, Agent]) -> None`
Execute one simulation step.

```python
from spacxt import tick

tick(graph, bus, agents)  # One round of agent negotiations
```

---

## 🛠️ Spatial Tools

### relate_near

Evaluate spatial proximity between two objects.

```python
from spacxt.tools.topo_tool import relate_near

rel = relate_near(
    node_a={"id": "chair", "pos": [1.0, 1.0, 0.5]},
    node_b={"id": "table", "pos": [1.5, 1.2, 0.75]},
    near_thresh=0.75
)
# Returns: {"r": "near", "a": "chair", "b": "table", "conf": 0.7, "props": {"dist": 0.54}}
```

#### Parameters
- `node_a: Dict[str, Any]` - First object (with id, pos)
- `node_b: Dict[str, Any]` - Second object (with id, pos)
- `near_thresh: float` - Distance threshold for "near" (default: 0.75)

#### Returns
- `Dict[str, Any]` - Relationship descriptor with type, confidence, properties

---

## 🎨 GUI Components

### SceneVisualizer

Interactive 3D visualization of spatial reasoning.

```python
from spacxt import SceneVisualizer

visualizer = SceneVisualizer(graph, bus, agents)
visualizer.run()  # Launch GUI
```

#### Methods

##### `__init__(scene_graph, bus, agents)`
Initialize visualizer with scene components.

##### `run() -> None`
Launch the interactive GUI application.

---

## 📝 Configuration Format

### Bootstrap JSON Schema

```json
{
  "scene": {
    "id": "scene_identifier",
    "frame": "map",
    "rooms": [
      {
        "id": "room_id",
        "bbox": {
          "min": [x_min, y_min, z_min],
          "max": [x_max, y_max, z_max]
        }
      }
    ],
    "objects": [
      {
        "id": "object_id",
        "cls": "object_class",
        "pos": [x, y, z],
        "ori": [x, y, z, w],
        "bbox": {
          "type": "OBB",
          "xyz": [width, depth, height]
        },
        "aff": ["affordance1", "affordance2"],
        "lom": "mobility_level",
        "conf": 0.95,
        "state": {
          "custom_property": "value"
        }
      }
    ],
    "relations": [
      {
        "r": "relationship_type",
        "a": "source_object_id",
        "b": "target_object_id",
        "conf": 0.90
      }
    ]
  }
}
```

---

## 🔍 Usage Examples

### Basic Scene Setup

```python
import json
from spacxt import SceneGraph, Bus, make_agents, tick

# Load scene
with open("scene.json", "r") as f:
    data = json.load(f)

# Initialize components
graph = SceneGraph()
graph.load_bootstrap(data)

bus = Bus()
agent_ids = [obj["id"] for obj in data["scene"]["objects"]]
agents = make_agents(graph, bus, agent_ids)

# Run simulation
for i in range(10):
    tick(graph, bus, agents)

# Check discovered relationships
for (r, a, b), rel in graph.relations.items():
    if r != "in":  # Skip bootstrap relationships
        print(f"{a} {r} {b} (confidence: {rel.conf:.2f})")
```

### Custom Spatial Tool

```python
def relate_above(node_a, node_b, height_thresh=0.1):
    """Check if node_a is above node_b."""
    height_diff = node_a["pos"][2] - node_b["pos"][2]

    if height_diff > height_thresh:
        conf = min(0.9, height_diff / 1.0)  # Scale confidence
        return {
            "r": "above",
            "a": node_a["id"],
            "b": node_b["id"],
            "conf": conf,
            "props": {"height_diff": height_diff}
        }
    else:
        return {
            "r": "not_above",
            "a": node_a["id"],
            "b": node_b["id"],
            "conf": 0.8,
            "props": {"height_diff": height_diff}
        }

# Use in agent perception
class CustomAgent(Agent):
    def perceive_and_propose(self):
        # Standard near/far relationships
        super().perceive_and_propose()

        # Custom above/below relationships
        me = self.graph.get_node(self.id)
        neighbors = self.graph.neighbors(self.id, radius=2.0)

        for nb in neighbors:
            rel = relate_above(me.__dict__, nb.__dict__)
            if rel["r"] == "above" and rel["conf"] > 0.6:
                msg = A2AMessage(
                    type="RELATION_PROPOSE",
                    sender=self.id,
                    receiver=nb.id,
                    payload={"relation": rel}
                )
                self.send(msg)
```

### Dynamic Scene Modification

```python
from spacxt import GraphPatch

# Add new object
new_node = Node(
    id="lamp_1",
    cls="lamp",
    pos=(3.0, 1.0, 1.2),
    ori=(0, 0, 0, 1),
    bbox={"type": "OBB", "xyz": [0.3, 0.3, 1.2]},
    conf=0.95
)

patch = GraphPatch()
patch.add_nodes["lamp_1"] = new_node
graph.apply_patch(patch)

# Create agent for new object
new_agent = Agent(
    id="lamp_1",
    cls="lamp",
    graph=graph,
    send=bus.send,
    inbox=[]
)
agents["lamp_1"] = new_agent

# Continue simulation with new object
tick(graph, bus, agents)
```

---

## 🚨 Error Handling

### Common Exceptions

```python
try:
    graph.load_bootstrap(invalid_data)
except KeyError as e:
    print(f"Missing required field in bootstrap: {e}")

try:
    node = graph.get_node("nonexistent_id")
    if node is None:
        print("Node not found")
except Exception as e:
    print(f"Graph access error: {e}")

try:
    tick(graph, bus, agents)
except Exception as e:
    print(f"Simulation error: {e}")
```

### Validation

```python
def validate_node(node_data):
    required_fields = ["id", "cls", "pos", "ori", "bbox"]
    for field in required_fields:
        if field not in node_data:
            raise ValueError(f"Missing required field: {field}")

    if len(node_data["pos"]) != 3:
        raise ValueError("Position must be 3D coordinate")

    if len(node_data["ori"]) != 4:
        raise ValueError("Orientation must be quaternion (4 values)")

# Use before loading bootstrap
for obj in data["scene"]["objects"]:
    validate_node(obj)
```

---

*This API reference covers the core functionality. For advanced usage patterns and examples, see the [Examples](examples.md) documentation.*
