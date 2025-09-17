#!/usr/bin/env python3
"""
SpacXT Demo without LLM - Shows fallback to rule-based parsing.

This demo demonstrates that SpacXT works perfectly fine without LLM integration,
using rule-based natural language parsing as a fallback.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import SpacXT components
from src.spacxt import SceneGraph, Bus, make_agents, tick, SceneVisualizer

def main():
    print("🚀 Starting SpacXT Demo (No LLM Required)...")

    # Make sure no .env file interferes
    if os.path.exists('.env'):
        print("📝 Note: .env file detected - LLM features may be available")
    else:
        print("📝 Note: No .env file - using rule-based parsing (works great!)")

    try:
        # Load bootstrap configuration
        with open('bootstrap.json', 'r') as f:
            bootstrap = json.load(f)
        print("✅ Loaded scene configuration")

        # Initialize scene graph
        graph = SceneGraph()
        graph.load_bootstrap(bootstrap)
        print(f"✅ Initialized scene with {len(graph.nodes)} objects")

        # Create message bus and agents
        bus = Bus()
        agents = make_agents(graph, bus.send)
        print(f"✅ Created {len(agents)} agents")

        print("🎯 Launching interactive visualizer...")
        print()
        print("💡 Try these commands (work without LLM):")
        print("   • put a cup on the table")
        print("   • add a book near the chair")
        print("   • move the chair to the stove")
        print("   • remove the cup")
        print()

        # Launch GUI
        visualizer = SceneVisualizer(graph, bus, agents)
        visualizer.run()

    except FileNotFoundError:
        print("❌ Error: bootstrap.json not found")
        print("   Make sure you're running from the examples/ directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
