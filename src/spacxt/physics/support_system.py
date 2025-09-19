"""
Support Dependency System for SpacXT - tracks and manages object support relationships.

This system ensures that when a supporting object is removed, all objects that were
sitting on it will fall to the ground due to gravity.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from ..core.graph_store import SceneGraph, GraphPatch
from .physics_utils import PhysicsUtils, BoundingBox


class SupportTracker:
    """Tracks which objects are supported by which other objects."""

    def __init__(self):
        # Maps: supported_object_id -> supporting_object_id
        self.support_relationships: Dict[str, str] = {}
        # Maps: supporting_object_id -> set of supported_object_ids
        self.dependents: Dict[str, Set[str]] = {}

    def add_support(self, supported_id: str, supporting_id: str):
        """Record that supported_id is supported by supporting_id."""
        # Remove any existing support for this object
        self.remove_support(supported_id)

        # Add new support relationship
        self.support_relationships[supported_id] = supporting_id

        if supporting_id not in self.dependents:
            self.dependents[supporting_id] = set()
        self.dependents[supporting_id].add(supported_id)

    def remove_support(self, supported_id: str):
        """Remove support relationship for an object."""
        if supported_id in self.support_relationships:
            supporting_id = self.support_relationships[supported_id]
            del self.support_relationships[supported_id]

            if supporting_id in self.dependents:
                self.dependents[supporting_id].discard(supported_id)
                if not self.dependents[supporting_id]:
                    del self.dependents[supporting_id]

    def get_supporting_object(self, object_id: str) -> Optional[str]:
        """Get the object that supports the given object."""
        return self.support_relationships.get(object_id)

    def get_dependent_objects(self, supporting_id: str) -> Set[str]:
        """Get all objects that depend on the given supporting object (direct dependents only)."""
        return self.dependents.get(supporting_id, set()).copy()

    def get_all_dependent_objects_recursive(self, supporting_id: str) -> Set[str]:
        """Get all objects that depend on the given supporting object, including indirect dependents (recursive)."""
        all_dependents = set()

        def collect_dependents(current_supporter: str):
            direct_dependents = self.dependents.get(current_supporter, set())
            for dependent in direct_dependents:
                if dependent not in all_dependents:  # Avoid infinite loops
                    all_dependents.add(dependent)
                    # Recursively collect dependents of this dependent
                    collect_dependents(dependent)

        collect_dependents(supporting_id)
        return all_dependents

    def remove_object_completely(self, object_id: str) -> Set[str]:
        """
        Remove an object and return all objects that were depending on it.
        This is used when an object is removed from the scene.
        """
        dependents = self.get_dependent_objects(object_id)

        # Remove this object as a supporter
        if object_id in self.dependents:
            del self.dependents[object_id]

        # Remove this object as a dependent
        self.remove_support(object_id)

        # Remove support relationships for all its dependents
        for dependent_id in dependents:
            self.remove_support(dependent_id)

        return dependents

    def get_support_info(self) -> Dict[str, Any]:
        """Get debug information about current support relationships."""
        return {
            "support_relationships": dict(self.support_relationships),
            "dependents": {k: list(v) for k, v in self.dependents.items()},
            "total_supported_objects": len(self.support_relationships),
            "total_supporting_objects": len(self.dependents)
        }


class GravitySimulator:
    """Simulates gravity effects when objects lose their support."""

    def __init__(self, scene_graph: SceneGraph):
        self.graph = scene_graph
        self.physics = PhysicsUtils()

    def apply_gravity_to_objects(self, object_ids: List[str]) -> List[Tuple[str, Tuple[float, float, float]]]:
        """
        Apply gravity to unsupported objects, making them fall to the ground.

        Returns:
            List of (object_id, new_position) tuples for objects that moved
        """
        moved_objects = []

        for object_id in object_ids:
            if object_id not in self.graph.nodes:
                continue

            node = self.graph.nodes[object_id]
            current_pos = node.pos
            object_size = node.bbox['xyz']

            # Calculate ground position
            ground_pos = self.physics.align_to_ground(current_pos, object_size)

            # Only move if the object is not already on the ground
            if abs(current_pos[2] - ground_pos[2]) > 0.01:  # 1cm tolerance
                moved_objects.append((object_id, ground_pos))

        return moved_objects

    def apply_gravity_with_collision_detection(self, object_ids: List[str]) -> List[Tuple[str, Tuple[float, float, float]]]:
        """
        Apply gravity with collision detection to avoid objects landing inside each other.

        Returns:
            List of (object_id, new_position) tuples for objects that moved
        """
        from .collision_detector import collision_detector
        moved_objects = []

        # Sync collision detector with current scene
        collision_detector.collision_boxes.clear()
        for node_id, node in self.graph.nodes.items():
            if node_id not in object_ids:  # Don't include falling objects
                size = self.physics.ensure_minimum_size(node.bbox['xyz'])
                collision_detector.add_object(node_id, node.pos, size)

        # Apply gravity to each object
        for object_id in object_ids:
            if object_id not in self.graph.nodes:
                continue

            node = self.graph.nodes[object_id]
            current_pos = node.pos
            object_size = self.physics.ensure_minimum_size(node.bbox['xyz'])

            # Calculate desired ground position
            ground_pos = self.physics.align_to_ground(current_pos, object_size)

            # Only process if the object needs to fall
            if abs(current_pos[2] - ground_pos[2]) > 0.01:  # 1cm tolerance
                # Find safe position using collision detection
                safe_pos = collision_detector.find_safe_position(
                    object_size=object_size,
                    preferred_position=ground_pos,
                    search_radius=0.5,  # 50cm search radius
                    max_attempts=10
                )

                if safe_pos:
                    moved_objects.append((object_id, safe_pos))
                    # Add this object to collision detector for subsequent objects
                    collision_detector.add_object(object_id, safe_pos, object_size)
                else:
                    # Fallback to simple ground position
                    moved_objects.append((object_id, ground_pos))
                    collision_detector.add_object(object_id, ground_pos, object_size)

        return moved_objects


class SupportSystem:
    """Main support system that combines tracking and gravity simulation."""

    def __init__(self, scene_graph: SceneGraph):
        self.graph = scene_graph
        self.support_tracker = SupportTracker()
        self.gravity_simulator = GravitySimulator(scene_graph)
        self.physics = PhysicsUtils()

    def analyze_and_update_support_relationships(self):
        """
        Analyze the current scene and update support relationships based on spatial positions.
        This should be called after objects are added or moved.
        """
        # Clear existing relationships
        self.support_tracker = SupportTracker()

        # Analyze all objects to detect support relationships
        for object_id, node in self.graph.nodes.items():
            supporting_object = self._find_supporting_object(object_id, node)
            if supporting_object:
                self.support_tracker.add_support(object_id, supporting_object)

    def _find_supporting_object(self, object_id: str, node) -> Optional[str]:
        """
        Find what object (if any) is supporting the given object.
        An object is supported if it's sitting on top of another object.
        """
        object_bbox = BoundingBox(node.pos, node.bbox['xyz'])

        # Check if object is on the ground (not supported by anything)
        ground_z = self.physics.GROUND_LEVEL + node.bbox['xyz'][2]/2
        if abs(node.pos[2] - ground_z) < 0.05:  # 5cm tolerance
            return None  # Object is on ground, not supported

        # Look for objects that could be supporting this one
        best_supporter = None
        best_support_level = -1

        for other_id, other_node in self.graph.nodes.items():
            if other_id == object_id:
                continue

            other_bbox = BoundingBox(other_node.pos, other_node.bbox['xyz'])

            # Check if this object could be supporting our object
            if self._is_object_supported_by(object_bbox, other_bbox):
                # Prefer larger supporting surfaces when heights are similar
                # This prevents books from "supporting" each other when they're both on a table
                if best_supporter is None:
                    best_supporter = other_id
                    best_support_level = other_bbox.top_level
                else:
                    # If heights are very similar (within 5cm), prefer the larger surface
                    height_diff = abs(other_bbox.top_level - best_support_level)
                    if height_diff < 0.05:  # 5cm tolerance
                        current_surface_area = other_bbox.size[0] * other_bbox.size[1]
                        best_surface_area = self.graph.nodes[best_supporter].bbox['xyz'][0] * self.graph.nodes[best_supporter].bbox['xyz'][1]
                        if current_surface_area > best_surface_area:
                            best_supporter = other_id
                            best_support_level = other_bbox.top_level
                    elif other_bbox.top_level > best_support_level:
                        # Clear height difference - choose the higher one
                        best_supporter = other_id
                        best_support_level = other_bbox.top_level

        return best_supporter

    def _is_object_supported_by(self, object_bbox: BoundingBox, potential_supporter_bbox: BoundingBox) -> bool:
        """Check if object_bbox is supported by potential_supporter_bbox."""

        # Check horizontal overlap (object must be above the supporter)
        x_distance = abs(object_bbox.center[0] - potential_supporter_bbox.center[0])
        y_distance = abs(object_bbox.center[1] - potential_supporter_bbox.center[1])
        x_threshold = (object_bbox.size[0]/2 + potential_supporter_bbox.size[0]/2)
        y_threshold = (object_bbox.size[1]/2 + potential_supporter_bbox.size[1]/2)

        x_overlap = x_distance < x_threshold
        y_overlap = y_distance < y_threshold

        if not (x_overlap and y_overlap):
            return False

        # Check vertical alignment (object should be sitting on top)
        expected_z = potential_supporter_bbox.top_level + object_bbox.size[2]/2
        actual_z = object_bbox.center[2]
        z_difference = abs(actual_z - expected_z)

        # Allow some tolerance for floating point precision and placement variations
        z_tolerance = 0.1  # 10cm tolerance
        return z_difference < z_tolerance

    def handle_object_removal(self, removed_object_id: str) -> Tuple[List[str], List[Tuple[str, Tuple[float, float, float]]]]:
        """
        Handle the removal of an object and apply gravity to dependent objects.

        Returns:
            Tuple of (affected_object_ids, moved_objects_list)
            where moved_objects_list contains (object_id, new_position) pairs
        """

        # Get all objects that were depending on the removed object (recursively)
        all_dependent_objects = self.support_tracker.get_all_dependent_objects_recursive(removed_object_id)

        # Remove the object and all its support relationships
        direct_dependents = self.support_tracker.remove_object_completely(removed_object_id)

        if not all_dependent_objects:
            return [], []

        # Apply gravity to all affected objects (both direct and indirect dependents)
        moved_objects = self.gravity_simulator.apply_gravity_with_collision_detection(
            list(all_dependent_objects)
        )

        # Re-analyze support relationships after gravity simulation
        self.analyze_and_update_support_relationships()

        return list(all_dependent_objects), moved_objects

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the support system."""
        support_info = self.support_tracker.get_support_info()

        # Add scene analysis
        total_objects = len(self.graph.nodes)
        ground_objects = 0
        supported_objects = len(support_info["support_relationships"])

        for node_id, node in self.graph.nodes.items():
            ground_z = self.physics.GROUND_LEVEL + node.bbox['xyz'][2]/2
            if abs(node.pos[2] - ground_z) < 0.05:
                ground_objects += 1

        # Add recursive dependency information
        recursive_dependents = {}
        for supporter_id in support_info["dependents"].keys():
            recursive_deps = self.support_tracker.get_all_dependent_objects_recursive(supporter_id)
            if recursive_deps:
                recursive_dependents[supporter_id] = list(recursive_deps)

        return {
            **support_info,
            "recursive_dependents": recursive_dependents,
            "scene_analysis": {
                "total_objects": total_objects,
                "ground_objects": ground_objects,
                "supported_objects": supported_objects,
                "floating_objects": total_objects - ground_objects - supported_objects
            }
        }
