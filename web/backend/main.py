"""
SpacXT Web Backend - FastAPI Service
Professional spatial context management API
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime

# Import our spatial context system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from spacxt.core.graph_store import SceneGraph, Node, Relation, GraphPatch
from spacxt.core.agents import Agent
from spacxt.core.orchestrator import Bus, make_agents, tick
from spacxt.nlp.llm_parser import LLMCommandParser
from spacxt.nlp.scene_modifier import SceneModifier
from spacxt.nlp.spatial_qa import SpatialQASystem
from spacxt.physics.support_system import SupportSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="SpacXT Spatial Context API",
    description="Professional spatial context management and natural language interface",
    version="1.0.0"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ObjectCreate(BaseModel):
    object_type: str
    position: Optional[List[float]] = None
    target_object: Optional[str] = None
    spatial_relation: Optional[str] = "on_ground"
    quantity: int = 1

class ObjectMove(BaseModel):
    object_id: str
    target_object: Optional[str] = None
    position: Optional[List[float]] = None
    spatial_relation: Optional[str] = "near"

class NLCommand(BaseModel):
    command: str
    session_id: Optional[str] = "default"

class SpatialQuestion(BaseModel):
    question: str
    session_id: Optional[str] = "default"

class SceneResponse(BaseModel):
    objects: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    support_relationships: Dict[str, Any]
    timestamp: str

# Global state management
class SpatialContextManager:
    def __init__(self):
        self.sessions = {}
        self.websocket_connections = []
        self.simulation_tasks = {}  # Background simulation tasks per session
        self.activity_logs = {}  # Activity logs per session

    def get_session(self, session_id: str = "default"):
        if session_id not in self.sessions:
            # Initialize new session
            scene_graph = SceneGraph()
            bus = Bus()

            # Load default scene
            self._load_default_scene(scene_graph)

            # Create agents for all objects in the scene
            object_ids = list(scene_graph.nodes.keys())
            agents = make_agents(scene_graph, bus, object_ids)

            # Initialize systems
            command_parser = LLMCommandParser()
            scene_modifier = SceneModifier(scene_graph, bus, agents)
            qa_system = SpatialQASystem(scene_graph, scene_modifier.support_system)

            self.sessions[session_id] = {
                'scene_graph': scene_graph,
                'bus': bus,
                'agents': agents,
                'scene_modifier': scene_modifier,
                'command_parser': command_parser,
                'qa_system': qa_system,
                'last_updated': datetime.now(),
                'simulation_running': False
            }

            # Initialize activity log for this session
            self.activity_logs[session_id] = []

            # Start continuous agent simulation
            self._start_agent_simulation(session_id)

        return self.sessions[session_id]

    def _load_default_scene(self, scene_graph: SceneGraph):
        """Load a default scene with some objects"""
        # Table
        table_node = Node(
            id="table_1",
            cls="furniture",
            pos=(2.0, 2.0, 0.375),  # Properly grounded
            ori=(0, 0, 0, 1),
            bbox={'type': 'OBB', 'xyz': [1.2, 0.8, 0.75]},
            aff=['support'],
            lom='large',
            conf=0.9,
            state={},
            meta={'color': 'brown', 'material': 'wood'}
        )

        # Chair
        chair_node = Node(
            id="chair_1",
            cls="furniture",
            pos=(1.0, 3.0, 0.45),
            ori=(0, 0, 0, 1),
            bbox={'type': 'OBB', 'xyz': [0.5, 0.5, 0.9]},
            aff=['support'],
            lom='medium',
            conf=0.9,
            state={},
            meta={'color': 'blue', 'material': 'plastic'}
        )

        # Stove
        stove_node = Node(
            id="stove_1",
            cls="appliance",
            pos=(4.0, 1.5, 0.45),
            ori=(0, 0, 0, 1),
            bbox={'type': 'OBB', 'xyz': [0.7, 0.6, 0.9]},
            aff=['heat', 'support'],
            lom='large',
            conf=0.9,
            state={'temperature': 'off'},
            meta={'color': 'silver', 'material': 'steel'}
        )

        # Apply to scene
        patch = GraphPatch()
        patch.add_nodes = {
            "table_1": table_node,
            "chair_1": chair_node,
            "stove_1": stove_node
        }
        scene_graph.apply_patch(patch)

    def _start_agent_simulation(self, session_id: str):
        """Start continuous agent simulation for a session"""
        if session_id in self.simulation_tasks:
            return  # Already running

        async def simulation_loop():
            session = self.get_session(session_id)
            session['simulation_running'] = True

            self._log_activity(session_id, "🤖 Agent simulation started", "system")

            while session['simulation_running']:
                try:
                    # Run one agent negotiation tick
                    old_relations_count = len(session['scene_graph'].relations)

                    # Capture messages before tick
                    pre_tick_messages = []
                    for agent_id, agent in session['agents'].items():
                        if agent.inbox:
                            pre_tick_messages.extend([
                                f"📨 {agent_id} received {len(agent.inbox)} messages"
                            ])

                    # Run the tick
                    tick(session['scene_graph'], session['bus'], session['agents'])

                    # Check for relationship changes
                    new_relations_count = len(session['scene_graph'].relations)
                    if new_relations_count != old_relations_count:
                        change = new_relations_count - old_relations_count
                        if change > 0:
                            self._log_activity(session_id, f"🔗 +{change} spatial relationships discovered", "agent")
                        else:
                            self._log_activity(session_id, f"🔗 {abs(change)} spatial relationships removed", "agent")

                        # Broadcast scene update ONLY when relationships change
                        await self.broadcast_scene_update(session_id)
                    # If no relationship changes, don't broadcast to avoid unnecessary graph updates

                    # Log agent activities if any
                    for msg in pre_tick_messages:
                        self._log_activity(session_id, msg, "agent")

                    # Wait before next tick - longer interval to reduce updates
                    await asyncio.sleep(10.0)  # 10 second intervals (less aggressive)

                except Exception as e:
                    logger.error(f"Simulation error for session {session_id}: {e}")
                    self._log_activity(session_id, f"⚠️ Simulation error: {str(e)}", "error")
                    await asyncio.sleep(5.0)  # Longer wait on error

            self._log_activity(session_id, "🛑 Agent simulation stopped", "system")

        # Start the simulation task
        task = asyncio.create_task(simulation_loop())
        self.simulation_tasks[session_id] = task

    def _stop_agent_simulation(self, session_id: str):
        """Stop agent simulation for a session"""
        if session_id in self.sessions:
            self.sessions[session_id]['simulation_running'] = False

        if session_id in self.simulation_tasks:
            task = self.simulation_tasks[session_id]
            task.cancel()
            del self.simulation_tasks[session_id]

    def _log_activity(self, session_id: str, message: str, activity_type: str = "info"):
        """Log activity for a session"""
        if session_id not in self.activity_logs:
            self.activity_logs[session_id] = []

        activity_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "message": message
        }

        # Keep only last 100 entries per session
        self.activity_logs[session_id].append(activity_entry)
        if len(self.activity_logs[session_id]) > 100:
            self.activity_logs[session_id] = self.activity_logs[session_id][-100:]

        # Broadcast activity update
        asyncio.create_task(self._broadcast_activity_update(session_id, activity_entry))

    async def _broadcast_activity_update(self, session_id: str, activity_entry: dict):
        """Broadcast activity update to WebSocket clients"""
        if not self.websocket_connections:
            return

        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json({
                    "type": "activity_update",
                    "session_id": session_id,
                    "activity": activity_entry
                })
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)

    async def _trigger_immediate_relationship_update(self, session_id: str):
        """Trigger immediate agent negotiation to discover new relationships"""
        try:
            session = self.get_session(session_id)

            # Run 3 quick ticks to allow agents to discover new relationships
            for i in range(3):
                old_count = len(session['scene_graph'].relations)
                tick(session['scene_graph'], session['bus'], session['agents'])
                new_count = len(session['scene_graph'].relations)

                if new_count > old_count:
                    self._log_activity(session_id, f"🔍 Agents discovered {new_count - old_count} new relationships", "agent")

                await asyncio.sleep(0.1)  # Short delay between ticks

        except Exception as e:
            logger.error(f"Error in immediate relationship update: {e}")
            self._log_activity(session_id, f"⚠️ Error updating relationships: {str(e)}", "error")

    async def broadcast_scene_update(self, session_id: str):
        """Broadcast scene updates to all connected WebSocket clients"""
        if not self.websocket_connections:
            return

        session = self.get_session(session_id)
        scene_data = self._serialize_scene(session, session_id)

        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json({
                    "type": "scene_update",
                    "data": scene_data
                })
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)

    def _serialize_scene(self, session, session_id: str = None):
        """Convert scene to JSON-serializable format"""
        scene_graph = session['scene_graph']
        support_system = session['scene_modifier'].support_system

        # Get objects
        objects = {}
        for obj_id, node in scene_graph.nodes.items():
            objects[obj_id] = {
                'id': obj_id,
                'type': node.cls,
                'position': list(node.pos),
                'orientation': list(node.ori),
                'bbox': node.bbox,
                'affordances': node.aff,
                'level_of_mobility': node.lom,
                'confidence': node.conf,
                'state': node.state,
                'meta': node.meta
            }

        # Get relationships
        relationships = []
        for (rel_type, a, b), rel in scene_graph.relations.items():
            relationships.append({
                'type': rel_type,
                'from': a,
                'to': b,
                'confidence': rel.conf,
                'properties': getattr(rel, 'props', {})
            })

        # Get support relationships
        support_info = support_system.support_tracker.get_support_info()

        # Find session_id if not provided
        if session_id is None:
            # Try to find session_id by matching session object
            for sid, sess in self.sessions.items():
                if sess == session:
                    session_id = sid
                    break
            if session_id is None:
                session_id = 'default'

        return {
            'objects': objects,
            'relationships': relationships,
            'support_relationships': support_info,
            'timestamp': datetime.now().isoformat(),
            'activity_logs': self.activity_logs.get(session_id, [])[-20:]  # Last 20 activities
        }

# Global manager instance
spatial_manager = SpatialContextManager()

# API Endpoints

@app.get("/")
async def root():
    return {"message": "SpacXT Spatial Context API", "version": "1.0.0"}

@app.get("/api/scene/{session_id}")
async def get_scene(session_id: str = "default"):
    """Get current scene state"""
    session = spatial_manager.get_session(session_id)
    return spatial_manager._serialize_scene(session, session_id)

@app.post("/api/objects/{session_id}")
async def create_object(object_data: ObjectCreate, session_id: str = "default"):
    """Create a new object in the scene"""
    try:
        session = spatial_manager.get_session(session_id)
        scene_modifier = session['scene_modifier']

        # Use scene modifier to add object
        # Convert to command format
        from spacxt.nlp.llm_parser import ParsedCommand

        command = ParsedCommand(
            action="add",
            object_type=object_data.object_type,
            target_object=object_data.target_object,
            spatial_relation=object_data.spatial_relation,
            position=object_data.position,
            quantity=object_data.quantity
        )

        result = scene_modifier.execute_command(command)

        # Log the command execution
        spatial_manager._log_activity(session_id, f"➕ Added {object_data.object_type} to scene", "command")

        # Trigger immediate agent negotiations for new relationships
        await spatial_manager._trigger_immediate_relationship_update(session_id)

        # Broadcast update
        await spatial_manager.broadcast_scene_update(session_id)

        return {"success": True, "message": result, "scene": spatial_manager._serialize_scene(session, session_id)}

    except Exception as e:
        logger.error(f"Error creating object: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commands/{session_id}")
async def execute_nl_command(nl_command: NLCommand, session_id: str = "default"):
    """Execute a natural language command"""
    try:
        session = spatial_manager.get_session(session_id)
        scene_modifier = session['scene_modifier']
        command_parser = session['command_parser']

        # Parse and execute command
        parsed_command = command_parser.parse(nl_command.command)
        if not parsed_command:
            return {"success": False, "error": "Failed to parse command"}

        success, message = scene_modifier.execute_command(parsed_command)

        # Log the command execution
        spatial_manager._log_activity(session_id, f"💬 '{nl_command.command}' → {message}", "command")

        # Trigger immediate relationship updates if successful
        if success:
            await spatial_manager._trigger_immediate_relationship_update(session_id)

        # Broadcast update
        await spatial_manager.broadcast_scene_update(session_id)

        return {
            "success": success,
            "command": nl_command.command,
            "parsed": parsed_command.__dict__,
            "message": message,
            "scene": spatial_manager._serialize_scene(session, session_id)
        }

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/questions/{session_id}")
async def ask_spatial_question(question: SpatialQuestion, session_id: str = "default"):
    """Ask a spatial question about the scene"""
    try:
        session = spatial_manager.get_session(session_id)
        qa_system = session['qa_system']

        # Process question
        answer = qa_system.answer_spatial_question(question.question)

        return {
            "success": True,
            "question": question.question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activities/{session_id}")
async def get_activities(session_id: str = "default", limit: int = 50):
    """Get activity logs for a session"""
    try:
        activities = spatial_manager.activity_logs.get(session_id, [])
        return {
            "success": True,
            "activities": activities[-limit:] if limit > 0 else activities,
            "total": len(activities)
        }
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/objects/{session_id}/{object_id}")
async def delete_object(object_id: str, session_id: str = "default"):
    """Delete an object from the scene"""
    try:
        session = spatial_manager.get_session(session_id)
        scene_modifier = session['scene_modifier']

        # Use scene modifier to remove object
        from spacxt.nlp.llm_parser import ParsedCommand

        command = ParsedCommand(
            action="remove",
            object_id=object_id
        )

        result = scene_modifier.execute_command(command)

        # Broadcast update
        await spatial_manager.broadcast_scene_update(session_id)

        return {"success": True, "message": result, "scene": spatial_manager._serialize_scene(session, session_id)}

    except Exception as e:
        logger.error(f"Error deleting object: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate/{session_id}")
async def run_simulation_step(session_id: str = "default"):
    """Run one step of agent simulation"""
    try:
        session = spatial_manager.get_session(session_id)

        # Run one simulation tick
        tick(session['scene_graph'], session['bus'], session['agents'])

        # Broadcast update
        await spatial_manager.broadcast_scene_update(session_id)

        return {"success": True, "scene": spatial_manager._serialize_scene(session)}

    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()
    spatial_manager.websocket_connections.append(websocket)

    try:
        # Send initial scene state
        session = spatial_manager.get_session(session_id)
        scene_data = spatial_manager._serialize_scene(session, session_id)
        await websocket.send_json({
            "type": "scene_update",
            "data": scene_data
        })

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "command":
                    # Handle real-time commands
                    command = data.get("command", "")
                    if command:
                        scene_modifier = session['scene_modifier']
                        command_parser = session['command_parser']
                        parsed_command = command_parser.parse(command)
                        if parsed_command:
                            success, message = scene_modifier.execute_command(parsed_command)

                        # Broadcast to all clients
                        await spatial_manager.broadcast_scene_update(session_id)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in spatial_manager.websocket_connections:
            spatial_manager.websocket_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
