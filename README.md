
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

# Or using poetry
poetry install
```

### Run the Demo

```bash
cd examples
python demo.py
```

It will:
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
│   └── tools/                    # Spatial reasoning tools
│       └── topo_tool.py          # Simple spatial relations (near/far with confidence)
├── examples/                     # Example usage
│   ├── demo.py                   # Quick simulation
│   └── bootstrap.json            # Initial 3DSG
└── pyproject.toml               # Project configuration
```

## Next steps (drop-in upgrades)
- **MCP Tooling**: wrap `topo_tool` and graph patches behind a JSON-RPC (MCP) server; agents call tools instead of functions.
- **More relations**: `on_top_of`, `inside`, `supports`, `visible_from` using OBB tests / raycasts.
- **Uncertainty**: keep covariance per node; decay confidence; require confirmations on conflicts.
- **CRDTs**: adopt LWW-Element-Set or Delta-CRDTs for relations and attributes at scale.
- **Event bus**: replace in-memory bus with NATS/Redis/Kafka for real systems.
- **LLM tools**: expose `spatial_context()`, `query_object(id)`, `navigate(to)`, `sense(roi)`; keep JSON compact in prompts.
- **Rust core**: port `topo_tool` to Rust (rstar + nphysics or rapier) for performance.
```

