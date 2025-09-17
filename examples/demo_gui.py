#!/usr/bin/env python3
"""
SpacXT GUI Demo - Interactive 3D visualization of spatial reasoning.

This demo shows the same spatial context engine as demo.py, but with an
interactive 3D GUI that lets you visualize the scene, watch agent negotiations,
and interact with objects in real-time.

Features:
- 3D visualization of objects and their spatial relationships
- Real-time agent activity monitoring
- Interactive controls to start/stop simulation
- Move objects and see relationships update
- Clean, intuitive interface

Usage:
    python demo_gui.py
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import spacxt
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from spacxt import SceneGraph, Bus, make_agents, SceneVisualizer
except ImportError as e:
    print("❌ Error importing SpacXT components:")
    print(f"   {e}")
    print("\\n💡 Make sure you have the required dependencies installed:")
    print("   pip install matplotlib numpy")
    sys.exit(1)


def main():
    """Run the GUI demo."""
    print("🚀 Starting SpacXT GUI Demo...")

    try:
        # 1) Load bootstrap data
        bootstrap_path = Path(__file__).parent / "bootstrap.json"
        with open(bootstrap_path, "r") as f:
            data = json.load(f)
        print("✅ Loaded scene configuration")

        # 2) Initialize scene graph
        graph = SceneGraph()
        graph.load_bootstrap(data)
        print(f"✅ Initialized scene with {len(graph.nodes)} objects")

        # 3) Create message bus and agents
        bus = Bus()
        agent_ids = [obj["id"] for obj in data["scene"]["objects"]]
        agents = make_agents(graph, bus, agent_ids)
        print(f"✅ Created {len(agents)} agents")

        # 4) Launch GUI
        print("🎯 Launching interactive visualizer...")
        visualizer = SceneVisualizer(graph, bus, agents)
        visualizer.run()

    except FileNotFoundError:
        print("❌ Error: bootstrap.json not found")
        print("   Make sure you're running this from the examples/ directory")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        print("\n💡 Common fixes:")
        print("   - Make sure you have matplotlib and numpy installed: poetry install")
        print("   - Try running with: poetry run python demo_gui.py")
        print("   - Check that you're in the examples/ directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
