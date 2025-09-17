# Getting Started with SpacXT

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Poetry (recommended) or pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd spacxt

# Install with Poetry (recommended)
poetry install

# Or install with pip
pip install -e .
```

### Run the Demo

**Interactive GUI Demo (Recommended):**
```bash
cd examples
poetry run python demo_gui.py
```

**Command Line Demo:**
```bash
cd examples
poetry run python demo.py
```

## 🎮 Using the GUI Demo

### Main Interface
The GUI consists of three main areas:

1. **3D Scene View (Left)**: Interactive visualization of objects and relationships
2. **Controls (Right Top)**: Simulation controls and actions
3. **Information Panels (Right Bottom)**: Real-time data and activity logs

### Controls Explained

#### **Start Simulation**
- Begins autonomous agent negotiations
- Agents scan for neighbors and propose relationships
- Updates happen every 0.5 seconds
- Watch the **Agent Activity** panel for real-time negotiations

#### **Single Step**
- Execute one simulation tick manually
- Useful for debugging and understanding the process step-by-step
- See exactly what happens in each negotiation round

#### **Move Chair**
- Simulates an environmental change
- Moves the chair closer to the stove
- Agents automatically re-evaluate and update relationships
- Demonstrates dynamic adaptation

#### **Reset Scene**
- Returns all objects to initial positions
- Clears discovered relationships (keeps bootstrap "in" relationships)
- Stops any running simulation

### What to Watch For

#### **Spatial Relations Panel**
```
=== IN ===
  table_1 → kitchen (conf: 1.00)
  chair_12 → kitchen (conf: 1.00)
  stove → kitchen (conf: 1.00)

=== NEAR ===
  chair_12 → table_1 (conf: 0.70)
  table_1 → chair_12 (conf: 0.70)
```

#### **Agent Activity Panel**
```
12:34:56 🚀 Starting simulation...
12:34:57 Tick 1 | Negotiating... (Messages: 2)
12:34:58 🎉 Tick 2 | New spatial relations discovered! Total: 1
12:34:59 📦 Moved chair to new position
12:35:00 🎉 Tick 3 | New spatial relations discovered! Total: 2
```

#### **3D Visualization**
- **Brown box**: Table
- **Orange box**: Chair
- **Red box**: Stove
- **Green dashed lines**: "Near" relationships
- **Labels**: Object IDs and types

## 💻 Command Line Demo

The CLI demo runs the same spatial reasoning but outputs to the console:

```bash
$ poetry run python demo.py

Relations after initial negotiation:
('in', 'table_1', 'kitchen') {} conf= 1.0
('in', 'chair_12', 'kitchen') {} conf= 1.0
('in', 'stove', 'kitchen') {} conf= 1.0
('near', 'chair_12', 'table_1') {'dist': 0.68} conf= 0.7

Relations after chair moved:
('in', 'table_1', 'kitchen') {} conf= 1.0
('in', 'chair_12', 'kitchen') {} conf= 1.0
('in', 'stove', 'kitchen') {} conf= 1.0
('near', 'chair_12', 'table_1') {'dist': 1.2} conf= 0.4
('near', 'chair_12', 'stove') {'dist': 0.6} conf= 0.8

LLM Context JSON:
{
  "scene": {
    "frame": "map",
    "agent_pose": [2.7, 1.3, 1.6, 0, 0, 0, 1],
    "roi": "kitchen",
    "summary": "You are in kitchen. 3 objects nearby.",
    "objects": [...],
    "relations": [...],
    "notices": []
  }
}
```

## 🔧 Understanding the Scene Configuration

The demo uses `bootstrap.json` to define the initial scene:

```json
{
  "scene": {
    "id": "apt_101",
    "objects": [
      {
        "id": "table_1",
        "cls": "table",
        "pos": [1.5, 1.5, 0.75],
        "bbox": {"type": "OBB", "xyz": [1.2, 0.8, 0.75]},
        "conf": 0.98
      },
      {
        "id": "chair_12",
        "cls": "chair",
        "pos": [0.9, 1.6, 0.45],
        "bbox": {"type": "OBB", "xyz": [0.5, 0.5, 0.9]},
        "conf": 0.92
      }
    ],
    "relations": [
      {"r": "in", "a": "table_1", "b": "kitchen"},
      {"r": "in", "a": "chair_12", "b": "kitchen"}
    ]
  }
}
```

### Key Properties:
- **id**: Unique object identifier
- **cls**: Object class/type
- **pos**: 3D position [x, y, z]
- **bbox**: Bounding box dimensions
- **conf**: Confidence score (0.0-1.0)

## 🧠 Understanding Agent Behavior

### Perception Phase
Each agent scans within a **1.5-unit radius** for neighbors:

```python
neighbors = self.graph.neighbors(self.id, radius=1.5)
```

### Evaluation Phase
For each neighbor, agents use spatial tools to evaluate relationships:

```python
rel = relate_near(me.__dict__, neighbor.__dict__)
# Returns: {"r": "near", "conf": 0.7, "props": {"dist": 0.68}}
```

### Negotiation Phase
Agents send proposals and process responses:

```python
# Send proposal
msg = A2AMessage(
    type="RELATION_PROPOSE",
    sender=self.id,
    receiver=neighbor.id,
    payload={"relation": rel}
)

# Process response
if rel["conf"] >= 0.6:  # Acceptance threshold
    # Accept and add to scene graph
```

## 🎯 Experimentation Ideas

### 1. **Modify Object Positions**
Edit `bootstrap.json` to change initial positions:
```json
"pos": [2.0, 2.0, 0.75]  // Move table
```

### 2. **Adjust Parameters**
- **Neighbor radius**: Change detection range
- **Confidence threshold**: Adjust acceptance criteria
- **Near threshold**: Modify what's considered "near"

### 3. **Add New Objects**
```json
{
  "id": "lamp_1",
  "cls": "lamp",
  "pos": [3.0, 1.0, 1.2],
  "bbox": {"type": "OBB", "xyz": [0.3, 0.3, 1.2]}
}
```

### 4. **Create Custom Scenes**
Build your own spatial scenarios and watch agents discover relationships.

## 🚀 Next Steps

Once you're comfortable with the demo:

1. **Explore the Code**: Dive into the source to understand implementation
2. **Read Architecture**: Learn about the system design
3. **Check Examples**: See more advanced usage patterns
4. **Build Applications**: Create your own spatial reasoning systems

## 🔍 Troubleshooting

### GUI Won't Start
```bash
# Install GUI dependencies
poetry install

# Check matplotlib/numpy availability
python -c "import matplotlib, numpy; print('GUI deps OK')"
```

### No Relationships Discovered
- Check object positions in `bootstrap.json`
- Verify objects are within neighbor radius (1.5 units)
- Ensure distances are below near threshold (0.75 units)

### Performance Issues
- Reduce tick rate in GUI visualizer
- Limit number of objects in scene
- Use spatial indexing for large scenes

---

*Ready to go deeper? Check out the [API Reference](api-reference.md) for detailed technical documentation.*
