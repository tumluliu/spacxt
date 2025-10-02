"""
Scene Modifier for SpacXT - Executes parsed natural language commands.

Modifies the spatial scene based on structured commands from the CommandParser.
"""

import random
import math
from typing import Dict, Optional, Tuple, Any
from ..core.graph_store import SceneGraph, Node, GraphPatch
from ..core.orchestrator import Bus
from ..core.agents import Agent
from ..physics.placement_engine import PlacementEngine
from ..physics.support_system import SupportSystem
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

            # Furniture
            'chair': {
                'cls': 'chair',
                'bbox': {'type': 'OBB', 'xyz': [0.5, 0.5, 0.9]},  # Same as bootstrap chair
                'aff': ['sit'],
                'lom': 'medium',
                'conf': 0.92,
                'color': 'brown'
            },

            # Books and media
            'book': {
                'cls': 'book',
                'bbox': {'type': 'OBB', 'xyz': [0.23, 0.15, 0.03]},  # Laying flat: length x width x thickness
                'aff': ['readable', 'portable'],
                'lom': 'high',
                'conf': 0.96,
                'color': 'varied',
                'orientation': 'flat'  # Indicates this object should lay flat
            },
            'laptop': {
                'cls': 'laptop',
                'bbox': {'type': 'OBB', 'xyz': [0.35, 0.25, 0.03]},  # Laying flat: length x width x thickness
                'aff': ['computing', 'portable'],
                'lom': 'medium',
                'conf': 0.98,
                'color': 'black',
                'state': {'power': 'off', 'battery': 85},
                'orientation': 'flat'
            },
            'phone': {
                'cls': 'phone',
                'bbox': {'type': 'OBB', 'xyz': [0.15, 0.07, 0.01]},  # Laying flat: length x width x thickness
                'aff': ['communication', 'portable'],
                'lom': 'high',
                'conf': 0.97,
                'color': 'black',
                'state': {'battery': 78, 'signal': 'good'},
                'orientation': 'flat'
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
                'bbox': {'type': 'OBB', 'xyz': [0.30, 0.21, 0.001]},  # Laying flat: length x width x thickness
                'aff': ['writable', 'portable'],
                'lom': 'high',
                'conf': 0.82,
                'color': 'white',
                'orientation': 'flat'
            },
        }


class SceneModifier:
    """Modifies the spatial scene based on natural language commands."""

    def __init__(self, scene_graph: SceneGraph, bus: Bus, agents: Dict[str, Agent]):
        self.graph = scene_graph
        self.bus = bus
        self.agents = agents
        self.templates = ObjectTemplates.get_templates()
        self.placement_engine = PlacementEngine(scene_graph)
        self.support_system = SupportSystem(scene_graph)
        self.object_counter = {}  # Track object counts for unique IDs

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
        """Add new object(s) to the scene."""
        quantity = getattr(command, 'quantity', 1)
        added_objects = []

        for i in range(quantity):
            # Generate unique object ID for each instance
            if quantity > 1:
                current_count = self.object_counter.get(command.object_type, 0)
                object_id = f"{command.object_type}_{current_count + i + 1}"
            else:
                object_id = command.object_id or f"{command.object_type}_1"

            # Use LLM-enhanced properties if available, but prioritize templates for objects with specific orientation needs
            if ('bbox' in command.properties and 'affordances' in command.properties and
                command.object_type not in ['book', 'laptop', 'phone', 'paper']):  # Objects that need proper orientation
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
                print(f"🔧 Using LLM properties for {command.object_type}: {template['bbox']}")
            elif command.object_type in self.templates:
                # Use template
                template = self.templates[command.object_type].copy()
                print(f"📋 Using template for {command.object_type}: {template['bbox']}")
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
                print(f"❓ Using default template for unknown {command.object_type}: {template['bbox']}")

            # Use physics engine for proper positioning
            object_size = template['bbox']['xyz']
            placement_type = self._get_placement_type(command)

            # Use LLM-calculated position for custom spatial relations
            if command.spatial_relation == 'custom' and command.position:
                # LLM provided exact position - use it with physics validation
                position = self.placement_engine.validate_and_adjust_position(
                    position=command.position,
                    object_size=object_size,
                    object_id=object_id
                )

                # Log the spatial reasoning
                spatial_desc = command.properties.get('spatial_description', 'custom placement')
                self._log_spatial_reasoning(f"LLM calculated position for {object_id}: {spatial_desc}")

            else:
                # Use physics engine for standard placements
                position = self.placement_engine.place_object(
                    object_id=object_id,
                    object_size=object_size,
                    placement_type=placement_type,
                    target_id=command.target_object,
                    randomness=0.3
                )

            # Create new node (position will be auto-corrected by SceneGraph physics)
            # Generate a readable name for the object
            object_name = f"{command.object_type.replace('_', ' ').title()} {object_counter + 1}"

            node = Node(
                id=object_id,
                name=object_name,  # Add human-readable name
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
            patch.add_nodes[object_id] = node
            self.graph.apply_patch(patch)

            # Create agent for new object
            agent = Agent(
                id=object_id,
                cls=template['cls'],
                graph=self.graph,
                send=self.bus.send,
                inbox=[]
            )
            self.agents[object_id] = agent

            # Add room relationship
            patch = GraphPatch()
            from ..core.graph_store import Relation
            room_rel = Relation(r="in", a=object_id, b="kitchen", conf=1.0)
            patch.add_relations.append(room_rel)
            self.graph.apply_patch(patch)

            added_objects.append(object_id)

        # Update support relationships after adding objects
        self.support_system.analyze_and_update_support_relationships()

        # Update object counter
        if command.object_type not in self.object_counter:
            self.object_counter[command.object_type] = 0
        self.object_counter[command.object_type] += quantity

        if quantity == 1:
            return True, f"Added {command.object_type} '{added_objects[0]}' to the scene"
        else:
            return True, f"Added {quantity} {command.object_type}s to the scene: {', '.join(added_objects)}"

    def _move_object(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Move existing object(s) - supports moving multiple objects of the same type."""

        # Handle quantity-based moves (e.g., "move the two cups")
        if command.quantity > 1 and command.object_type:
            return self._move_multiple_objects(command)

        # Single object move
        # Try different strategies to find the object
        object_id = None

        # Strategy 1: Use object_id if provided and not null
        if command.object_id and command.object_id.lower() not in ['null', 'none', '']:
            object_id = self._find_object_by_name(command.object_id)

        # Strategy 2: If object_id not found, try by object_type
        if not object_id and command.object_type:
            # Find first object of this type
            for obj_id, node in self.graph.nodes.items():
                if (node.cls == command.object_type or
                    command.object_type in obj_id.lower() or
                    obj_id.lower().startswith(command.object_type.lower())):
                    object_id = obj_id
                    break

        # Strategy 3: Try fuzzy matching with common synonyms
        if not object_id and command.object_type:
            synonyms = {
                'table': ['table'],
                'cup': ['coffee_cup', 'cup'],
                'book': ['book'],
                'chair': ['chair'],
                'stove': ['stove'],
                'lamp': ['lamp']
            }

            for synonym in synonyms.get(command.object_type, [command.object_type]):
                for obj_id, node in self.graph.nodes.items():
                    if synonym in obj_id.lower() or synonym == node.cls:
                        object_id = obj_id
                        break
                if object_id:
                    break

        if not object_id:
            # List available objects for debugging
            available_objects = list(self.graph.nodes.keys())
            return False, f"Could not find object to move. Looking for: '{command.object_id or command.object_type}'. Available objects: {available_objects}"

        return self._move_single_object(object_id, command)

    def _move_multiple_objects(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Move multiple objects of the same type."""
        # Find objects of the specified type
        matching_objects = []
        for obj_id, node in self.graph.nodes.items():
            if node.cls == command.object_type or command.object_type in obj_id:
                matching_objects.append(obj_id)

        if len(matching_objects) < command.quantity:
            return False, f"Only found {len(matching_objects)} {command.object_type}(s), but you asked to move {command.quantity}"

        # Move the requested number of objects
        moved_objects = []
        for i in range(command.quantity):
            object_id = matching_objects[i]
            success, _ = self._move_single_object(object_id, command)
            if success:
                moved_objects.append(object_id)

        if moved_objects:
            # Update support relationships after moving objects
            self.support_system.analyze_and_update_support_relationships()
            return True, f"Moved {len(moved_objects)} {command.object_type}(s): {', '.join(moved_objects)}"
        else:
            return False, f"Failed to move any {command.object_type}s"

    def _move_single_object(self, object_id: str, command: ParsedCommand) -> Tuple[bool, str]:
        """Move a single object and all its dependent objects."""
        if object_id not in self.graph.nodes:
            return False, f"Object {object_id} not found in scene"

        node = self.graph.nodes[object_id]
        old_position = node.pos
        object_size = node.bbox['xyz']
        placement_type = self._get_placement_type(command)

        # FIRST: Ensure support relationships are current
        self.support_system.analyze_and_update_support_relationships()

        # Get all dependent objects recursively (including objects stacked on top of direct dependents)
        dependent_objects = self.support_system.support_tracker.get_all_dependent_objects_recursive(object_id)

        # Find target object if specified
        target_id = None
        if command.target_object and command.target_object.lower() not in ['null', 'none', '']:
            target_id = self._find_object_by_name(command.target_object)
            if not target_id:
                # Try to find by type
                for obj_id, obj_node in self.graph.nodes.items():
                    if (obj_node.cls == command.target_object or
                        command.target_object in obj_id.lower()):
                        target_id = obj_id
                        break

        # Calculate new position for the main object
        new_position = self.placement_engine.place_object(
            object_id=object_id,
            object_size=object_size,
            placement_type=placement_type,
            target_id=target_id,
            randomness=0.2
        )

        # Calculate the movement offset
        movement_offset = (
            new_position[0] - old_position[0],
            new_position[1] - old_position[1],
            new_position[2] - old_position[2]
        )

        # Update positions of the main object and all its dependents
        patch = GraphPatch()
        patch.update_nodes[object_id] = {"pos": new_position}

        # Move dependent objects with the same offset (maintaining their relative positions)
        moved_dependents = []
        for dep_id in dependent_objects:
            if dep_id in self.graph.nodes:
                dep_node = self.graph.nodes[dep_id]
                dep_old_pos = dep_node.pos
                dep_new_pos = (
                    dep_old_pos[0] + movement_offset[0],
                    dep_old_pos[1] + movement_offset[1],
                    dep_old_pos[2] + movement_offset[2]
                )
                patch.update_nodes[dep_id] = {"pos": dep_new_pos}
                moved_dependents.append(dep_id)

        # Apply all position updates
        self.graph.apply_patch(patch)

        # Update support relationships after movement
        self.support_system.analyze_and_update_support_relationships()

        # Prepare result message
        result_message = f"Moved {object_id} to new position"
        if moved_dependents:
            result_message += f" (also moved {len(moved_dependents)} dependent objects: {', '.join(moved_dependents)})"

        return True, result_message

    def _remove_object(self, command: ParsedCommand) -> Tuple[bool, str]:
        """Remove an object from the scene with cascade physics for dependent objects."""
        # Find object to remove using enhanced object finding
        object_id = None

        # Strategy 1: Use object_id if provided and not null
        if command.object_id and command.object_id.lower() not in ['null', 'none', '']:
            object_id = self._find_object_by_name(command.object_id)

        # Strategy 2: If object_id not found, try by object_type
        if not object_id and command.object_type:
            # Find first object of this type
            for obj_id, node in self.graph.nodes.items():
                if (node.cls == command.object_type or
                    command.object_type in obj_id.lower() or
                    obj_id.lower().startswith(command.object_type.lower())):
                    object_id = obj_id
                    break

        # Strategy 3: Try fuzzy matching with common synonyms
        if not object_id and command.object_type:
            synonyms = {
                'table': ['table'],
                'cup': ['coffee_cup', 'cup'],
                'book': ['book'],
                'chair': ['chair'],
                'stove': ['stove'],
                'lamp': ['lamp']
            }

            for synonym in synonyms.get(command.object_type, [command.object_type]):
                for obj_id, node in self.graph.nodes.items():
                    if synonym in obj_id.lower() or synonym == node.cls:
                        object_id = obj_id
                        break
                if object_id:
                    break

        if not object_id:
            # List available objects for debugging
            available_objects = list(self.graph.nodes.keys())
            return False, f"Could not find object to remove. Looking for: '{command.object_id or command.object_type}'. Available objects: {available_objects}"

        # First, analyze current support relationships
        self.support_system.analyze_and_update_support_relationships()

        # Handle cascade physics - find objects that will lose support
        dependent_objects, moved_objects = self.support_system.handle_object_removal(object_id)

        # Apply gravity effects to dependent objects
        if moved_objects:
            patch = GraphPatch()
            for obj_id, new_position in moved_objects:
                patch.update_nodes[obj_id] = {"pos": new_position}
            self.graph.apply_patch(patch)

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

        # Build result message
        result_msg = f"Removed {object_id} from the scene"

        if dependent_objects:
            fallen_objects = [obj_id for obj_id, _ in moved_objects]
            if fallen_objects:
                result_msg += f". {len(fallen_objects)} object(s) fell due to gravity: {', '.join(fallen_objects)}"
            else:
                result_msg += f". {len(dependent_objects)} dependent object(s) were affected"

        return True, result_msg

    def _get_placement_type(self, command: ParsedCommand) -> str:
        """Convert command spatial relation to placement type."""
        if command.spatial_relation == 'on_top_of':
            return 'on_top_of'
        elif command.spatial_relation == 'near':
            return 'near'
        elif command.spatial_relation == 'custom':
            return 'custom'  # Will be handled specially with LLM position
        elif command.action == 'move':
            return 'near' if command.target_object else 'ground'
        else:
            return 'ground'

    def _log_spatial_reasoning(self, message: str):
        """Log spatial reasoning decisions."""
        print(f"🧠 Spatial Reasoning: {message}")

    def validate_scene_physics(self) -> Dict[str, Tuple[float, float, float]]:
        """Validate and correct all object positions using physics engine."""
        return self.placement_engine.validate_all_positions()

    def force_ground_alignment(self) -> Dict[str, Tuple[float, float, float]]:
        """Force ALL objects to ground (emergency use only)."""
        return self.placement_engine.force_ground_alignment()

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
                # Get new object size to calculate proper placement
                new_obj_size = command.properties.get('bbox', {}).get('xyz', [0.1, 0.1, 0.1])
                if isinstance(new_obj_size, dict) and 'xyz' in new_obj_size:
                    new_obj_size = new_obj_size['xyz']

                # Place on top of target: target center + target height/2 + new object height/2
                return (
                    target_pos[0] + random.uniform(-0.15, 0.15),  # Slight randomness but keep on table
                    target_pos[1] + random.uniform(-0.15, 0.15),
                    target_pos[2] + target_size[2]/2 + new_obj_size[2]/2 + 0.01  # Proper stacking
                )
            elif command.spatial_relation == 'near':
                # Get new object size for proper ground positioning
                new_obj_size = command.properties.get('bbox', {}).get('xyz', [0.1, 0.1, 0.1])
                if isinstance(new_obj_size, dict) and 'xyz' in new_obj_size:
                    new_obj_size = new_obj_size['xyz']

                # Place near target on ground
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0.4, 0.7)
                return (
                    target_pos[0] + distance * math.cos(angle),
                    target_pos[1] + distance * math.sin(angle),
                    new_obj_size[2]/2  # Proper ground positioning
                )

        # Default: random position in scene
        new_obj_size = command.properties.get('bbox', {}).get('xyz', [0.1, 0.1, 0.1])
        if isinstance(new_obj_size, dict) and 'xyz' in new_obj_size:
            new_obj_size = new_obj_size['xyz']

        return (
            random.uniform(1.0, 4.0),
            random.uniform(0.5, 2.5),
            new_obj_size[2]/2  # Proper ground positioning
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
