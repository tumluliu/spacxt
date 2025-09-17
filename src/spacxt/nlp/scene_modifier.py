"""
Scene Modifier for SpacXT - Executes parsed natural language commands.

Modifies the spatial scene based on structured commands from the CommandParser.
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any
from ..core.graph_store import SceneGraph, Node, GraphPatch
from ..core.orchestrator import Bus
from ..core.agents import Agent
from .llm_parser import ParsedCommand


class ObjectTemplates:
    """Templates for creating realistic objects with proper dimensions and properties."""

    @staticmethod
    def get_templates() -> Dict[str, Dict[str, Any]]:
        """Get object templates with realistic dimensions and properties."""
        return {
            # Containers and dishes
            'coffee_cup': {
                'cls': 'cup',
                'bbox': {'type': 'OBB', 'xyz': [0.08, 0.08, 0.10]},
                'aff': ['hold_liquid', 'portable'],
                'lom': 'high',
                'conf': 0.95,
                'color': 'white'
            },
            'glass': {
                'cls': 'glass',
                'bbox': {'type': 'OBB', 'xyz': [0.07, 0.07, 0.12]},
                'aff': ['hold_liquid', 'portable', 'fragile'],
                'lom': 'high',
                'conf': 0.93,
                'color': 'transparent'
            },
            'plate': {
                'cls': 'plate',
                'bbox': {'type': 'OBB', 'xyz': [0.25, 0.25, 0.03]},
                'aff': ['support', 'portable'],
                'lom': 'medium',
                'conf': 0.94,
                'color': 'white'
            },
            'bowl': {
                'cls': 'bowl',
                'bbox': {'type': 'OBB', 'xyz': [0.18, 0.18, 0.08]},
                'aff': ['hold_food', 'portable'],
                'lom': 'medium',
                'conf': 0.92,
                'color': 'ceramic'
            },

            # Books and media
            'book': {
                'cls': 'book',
                'bbox': {'type': 'OBB', 'xyz': [0.15, 0.23, 0.03]},
                'aff': ['readable', 'portable'],
                'lom': 'high',
                'conf': 0.96,
                'color': 'varied'
            },
            'laptop': {
                'cls': 'laptop',
                'bbox': {'type': 'OBB', 'xyz': [0.35, 0.25, 0.03]},
                'aff': ['computing', 'portable'],
                'lom': 'medium',
                'conf': 0.98,
                'color': 'black',
                'state': {'power': 'off', 'battery': 85}
            },
            'phone': {
                'cls': 'phone',
                'bbox': {'type': 'OBB', 'xyz': [0.07, 0.15, 0.01]},
                'aff': ['communication', 'portable'],
                'lom': 'high',
                'conf': 0.97,
                'color': 'black',
                'state': {'battery': 78, 'signal': 'good'}
            },

            # Decorative items
            'lamp': {
                'cls': 'lamp',
                'bbox': {'type': 'OBB', 'xyz': [0.20, 0.20, 0.45]},
                'aff': ['lighting'],
                'lom': 'low',
                'conf': 0.94,
                'color': 'brass',
                'state': {'power': 'off', 'brightness': 0}
            },
            'vase': {
                'cls': 'vase',
                'bbox': {'type': 'OBB', 'xyz': [0.12, 0.12, 0.25]},
                'aff': ['decorative', 'hold_flowers'],
                'lom': 'low',
                'conf': 0.91,
                'color': 'ceramic'
            },
            'candle': {
                'cls': 'candle',
                'bbox': {'type': 'OBB', 'xyz': [0.05, 0.05, 0.15]},
                'aff': ['lighting', 'decorative'],
                'lom': 'medium',
                'conf': 0.89,
                'color': 'white',
                'state': {'lit': False}
            },

            # Food items
            'apple': {
                'cls': 'fruit',
                'bbox': {'type': 'OBB', 'xyz': [0.08, 0.08, 0.08]},
                'aff': ['edible', 'portable'],
                'lom': 'high',
                'conf': 0.88,
                'color': 'red'
            },
            'bottle': {
                'cls': 'bottle',
                'bbox': {'type': 'OBB', 'xyz': [0.06, 0.06, 0.22]},
                'aff': ['hold_liquid', 'portable'],
                'lom': 'medium',
                'conf': 0.93,
                'color': 'blue'
            },

            # Office items
            'pen': {
                'cls': 'pen',
                'bbox': {'type': 'OBB', 'xyz': [0.01, 0.15, 0.01]},
                'aff': ['writing', 'portable'],
                'lom': 'high',
                'conf': 0.85,
                'color': 'blue'
            },
            'paper': {
                'cls': 'paper',
                'bbox': {'type': 'OBB', 'xyz': [0.21, 0.30, 0.001]},
                'aff': ['writable', 'portable'],
                'lom': 'high',
                'conf': 0.82,
                'color': 'white'
            },
        }


class SceneModifier:
    """Modifies the spatial scene based on natural language commands."""

    def __init__(self, scene_graph: SceneGraph, bus: Bus, agents: Dict[str, Agent]):
        self.graph = scene_graph
        self.bus = bus
        self.agents = agents
        self.templates = ObjectTemplates.get_templates()

    def execute_command(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Execute a parsed command and return success status and message."""
        try:
            if command.action == 'add':
                return self._add_object(command)
            elif command.action == 'move':
                return self._move_object(command)
            elif command.action == 'remove':
                return self._remove_object(command)
            else:
                return False, f"Unknown action: {command.action}"

        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def _add_object(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Add a new object to the scene."""
        # Use LLM-enhanced properties if available, otherwise fall back to templates
        if 'bbox' in command.properties and 'affordances' in command.properties:
            # LLM provided enhanced properties
            template = {
                'cls': command.object_type,
                'bbox': command.properties['bbox'],
                'aff': command.properties.get('affordances', []),
                'lom': 'high' if command.properties.get('fragility') == 'high' else 'medium',
                'conf': command.properties.get('confidence', 0.9),
                'color': command.properties.get('color', 'default'),
                'material': command.properties.get('material', 'unknown'),
                'weight_kg': command.properties.get('weight_kg', 1.0)
            }
        elif command.object_type in self.templates:
            # Use template
            template = self.templates[command.object_type].copy()
        else:
            # Create basic template for unknown objects
            template = {
                'cls': command.object_type,
                'bbox': {'type': 'OBB', 'xyz': [0.1, 0.1, 0.1]},
                'aff': ['portable'],
                'lom': 'medium',
                'conf': 0.7,
                'color': 'gray'
            }

        # Determine position
        position = self._calculate_position(command)
        if not position:
            return False, f"Could not determine position for {command.object_type}"

        # Create new node
        node = Node(
            id=command.object_id,
            cls=template['cls'],
            pos=position,
            ori=(0, 0, 0, 1),  # Default orientation
            bbox=template['bbox'],
            aff=template.get('aff', []),
            lom=template.get('lom', 'medium'),
            conf=template.get('conf', 0.9),
            state=template.get('state', {}),
            meta={'color': template.get('color', 'default')}
        )

        # Add to scene graph
        patch = GraphPatch()
        patch.add_nodes[command.object_id] = node
        self.graph.apply_patch(patch)

        # Create agent for new object
        agent = Agent(
            id=command.object_id,
            cls=template['cls'],
            graph=self.graph,
            send=self.bus.send,
            inbox=[]
        )
        self.agents[command.object_id] = agent

        # Add room relationship
        patch = GraphPatch()
        from ..core.graph_store import Relation
        room_rel = Relation(r="in", a=command.object_id, b="kitchen", conf=1.0)
        patch.add_relations.append(room_rel)
        self.graph.apply_patch(patch)

        return True, f"Added {command.object_type} '{command.object_id}' to the scene"

    def _move_object(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Move an existing object."""
        # Find object to move (by partial ID match)
        object_id = self._find_object_by_name(command.object_id)
        if not object_id:
            return False, f"Could not find object: {command.object_id}"

        # Calculate new position
        position = self._calculate_position(command)
        if not position:
            return False, f"Could not determine new position"

        # Update object position
        patch = GraphPatch()
        patch.update_nodes[object_id] = {"pos": position}
        self.graph.apply_patch(patch)

        return True, f"Moved {object_id} to new position"

    def _remove_object(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Remove an object from the scene."""
        # Find object to remove
        object_id = self._find_object_by_name(command.object_id)
        if not object_id:
            return False, f"Could not find object: {command.object_id}"

        # Remove from agents
        if object_id in self.agents:
            del self.agents[object_id]

        # Remove from scene graph
        if object_id in self.graph.nodes:
            del self.graph.nodes[object_id]

        # Remove related relationships
        keys_to_remove = []
        for key in self.graph.relations.keys():
            if key[1] == object_id or key[2] == object_id:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.graph.relations[key]

        return True, f"Removed {object_id} from the scene"

    def _calculate_position(self, command: ParsedCommand) -> Optional[Tuple[float, float, float]]:
        """Calculate position for object based on command."""
        if command.target_object:
            # Find target object
            target_id = self._find_object_by_name(command.target_object)
            if not target_id or target_id not in self.graph.nodes:
                return None

            target_node = self.graph.nodes[target_id]
            target_pos = target_node.pos
            target_size = target_node.bbox['xyz']

            if command.spatial_relation == 'on_top_of':
                # Place on top of target
                return (
                    target_pos[0] + random.uniform(-0.2, 0.2),  # Slight randomness
                    target_pos[1] + random.uniform(-0.2, 0.2),
                    target_pos[2] + target_size[2]/2 + 0.05  # On top with small gap
                )
            elif command.spatial_relation == 'near':
                # Place near target
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0.3, 0.6)
                return (
                    target_pos[0] + distance * math.cos(angle),
                    target_pos[1] + distance * math.sin(angle),
                    0.05  # Small height above ground
                )

        # Default: random position in scene
        return (
            random.uniform(1.0, 4.0),
            random.uniform(0.5, 2.5),
            0.05
        )

    def _find_object_by_name(self, name: str) -> Optional[str]:
        """Find object ID by partial name match."""
        name_lower = name.lower()

        # Exact match first
        if name in self.graph.nodes:
            return name

        # Partial match in object IDs
        for obj_id in self.graph.nodes.keys():
            if name_lower in obj_id.lower():
                return obj_id

        # Match by class type
        for obj_id, node in self.graph.nodes.items():
            if name_lower in node.cls.lower():
                return obj_id

        return None
