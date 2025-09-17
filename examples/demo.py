
import json, time
import sys
from pathlib import Path

# Add the src directory to the path so we can import spacxt
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spacxt import SceneGraph, Bus, make_agents, tick, GraphPatch

# 1) Load bootstrap
with open("bootstrap.json","r") as f:
    data = json.load(f)

g = SceneGraph()
g.load_bootstrap(data)

# 2) Build bus + agents for the 3 objects
bus = Bus()
agent_ids = [o["id"] for o in data["scene"]["objects"]]
agents = make_agents(g, bus, agent_ids)

# 3) Run a few ticks (chair near table => propose "near" relation)
for i in range(3):
    tick(g, bus, agents)
    time.sleep(0.05)

print("Relations after initial negotiation:")
for k, rel in g.relations.items():
    print(k, rel.props, "conf=", rel.conf)

# 4) Simulate an event: chair moved closer to stove (state change)
chair = g.get_node("chair_12")
patch = GraphPatch()
patch.update_nodes["chair_12"] = {"pos": (2.8, 1.3, 0.45)}
g.apply_patch(patch)

# re-run ticks to update relations
for i in range(3):
    tick(g, bus, agents)
    time.sleep(0.05)

print("\nRelations after chair moved:")
for k, rel in g.relations.items():
    print(k, rel.props, "conf=", rel.conf)

# 5) Assemble LLM-ready context
ctx = g.as_llm_context(agent_pose=(2.7,1.3,1.6), roi="kitchen", K=5)
print("\nLLM Context JSON:")
print(json.dumps(ctx, indent=2))
