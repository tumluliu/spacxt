
# Spatial Context PoC

This is a **minimal runnable prototype** of the idea:
- 3D Scene Graph (3DSG) bootstrap
- Each object is an **Agent** that proposes spatial relations to neighbors via **A2A**
- A tiny **topological tool** estimates "near/far"
- An **Orchestrator** delivers A2A messages and applies **graph patches** (event-sourced, LWW-lite)
- Produces a **token-efficient JSON context** for LLM prompts

> MVP is pure Python to keep it simple. Swap `topo_tool.py` for a Rust or C++ module later.

## Installation

### Development Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd spacxt

# Install in development mode
pip install -e .

# Or using poetry (recommended)
poetry install
```

### 🧠 LLM-Powered Features (Optional)

For advanced natural language processing:

1. Get API key from [OpenRouter.ai](https://openrouter.ai/)
2. Create `.env` file:
   ```bash
   OPENROUTER_API_KEY=your_api_key_here
   ```
3. See [docs/llm-setup.md](docs/llm-setup.md) for details

### Run the Demos

**Interactive GUI Demo (Recommended):**
```bash
# With Poetry (recommended)
cd examples
poetry run python demo_gui.py

# Or with direct Python (requires matplotlib, numpy)
cd examples
python demo_gui.py
```

**Command Line Demo:**
```bash
# With Poetry
cd examples
poetry run python demo.py

# Or with direct Python
cd examples
python demo.py
```

**GUI Demo Features:**
- 🎯 **3D Visualization**: See objects as 3D boxes in their actual positions
- 🤖 **Real-time Agent Activity**: Watch agents negotiate spatial relationships
- 🎮 **Interactive Controls**: Start/stop simulation, move objects, reset scene
- 📊 **Live Relationship Panel**: Monitor spatial relations as they evolve
- 🔄 **Dynamic Updates**: See the scene change as agents reason about space
- 🧠 **LLM-Powered Natural Language**: Command the scene using natural language!
  - "put a coffee cup on the table"
  - "add a modern laptop to the workspace"
  - "move the chair closer to the stove"

**Command Line Demo:**
1. Load `bootstrap.json`
2. Spin up agents for `table_1`, `chair_12`, `stove`
3. Let them propose/ack "near" relations
4. Move the chair to a new pose (simulated event) and rerun negotiation
5. Print the resulting relations and an LLM-ready JSON context

## Project Structure

```
spacxt/
├── src/spacxt/                    # Main package
│   ├── core/                     # Core engine components
│   │   ├── graph_store.py        # Nodes, relations, patches, and LLM-context assembler
│   │   ├── agents.py             # Agent logic: propose relations, accept/deny, emit patches
│   │   └── orchestrator.py       # Message bus and tick loop
│   ├── protocols/                # Communication protocols
│   │   └── a2a_protocol.py       # A2A message data class
│   ├── tools/                    # Spatial reasoning tools
│   │   └── topo_tool.py          # Simple spatial relations (near/far with confidence)
│   └── gui/                      # Visualization components
│       └── visualizer.py         # 3D scene visualizer with tkinter/matplotlib
├── examples/                     # Example usage
│   ├── demo_gui.py               # Interactive 3D GUI demo
│   ├── demo.py                   # Command line demo
│   └── bootstrap.json            # Initial 3DSG
└── pyproject.toml               # Project configuration
```

## 📚 Documentation

For comprehensive documentation, examples, and advanced usage:

- **[📖 Complete Documentation](docs/README.md)** - Full documentation index
- **[🎯 Overview](docs/overview.md)** - Vision and core concepts
- **[🏗️ Architecture](docs/architecture.md)** - System design deep dive
- **[🚀 Getting Started](docs/getting-started.md)** - Installation and tutorials
- **[🧠 LLM Setup](docs/llm-setup.md)** - Natural language processing setup
- **[🔧 API Reference](docs/api-reference.md)** - Complete API documentation
- **[💡 Examples](docs/examples.md)** - Code examples and patterns
- **[🌍 Applications](docs/applications.md)** - Real-world use cases

## 🚀 Next Steps (Roadmap)

- **MCP Tooling**: wrap `topo_tool` and graph patches behind a JSON-RPC (MCP) server; agents call tools instead of functions.
- **More relations**: `on_top_of`, `inside`, `supports`, `visible_from` using OBB tests / raycasts.
- **Uncertainty**: keep covariance per node; decay confidence; require confirmations on conflicts.
- **CRDTs**: adopt LWW-Element-Set or Delta-CRDTs for relations and attributes at scale.
- **Event bus**: replace in-memory bus with NATS/Redis/Kafka for real systems.
- **LLM tools**: expose `spatial_context()`, `query_object(id)`, `navigate(to)`, `sense(roi)`; keep JSON compact in prompts.
- **Rust core**: port `topo_tool` to Rust (rstar + nphysics or rapier) for performance.

