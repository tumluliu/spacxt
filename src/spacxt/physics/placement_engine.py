"""
Placement Engine for SpacXT - handles all object positioning with physics-based ground alignment.
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any
from ..core.graph_store import SceneGraph, Node
from .physics_utils import PhysicsUtils, BoundingBox


class PlacementEngine:
    """Physics-based object placement engine with ground alignment and collision detection."""

    def __init__(self, scene_graph: SceneGraph):
        self.graph = scene_graph
        self.physics = PhysicsUtils()

    def place_object(self, object_id: str, object_size: Tuple[float, float, float],
                    placement_type: str, target_id: Optional[str] = None,
                    randomness: float = 0.15) -> Tuple[float, float, float]:
        """
        Place an object in the scene using physics-based positioning.

        Args:
            object_id: ID of the object to place
            object_size: (width, depth, height) of the object
            placement_type: "on_top_of", "near", "ground", or "random"
            target_id: ID of target object (for "on_top_of" and "near")
            randomness: Amount of random offset (0.0 to 1.0)

        Returns:
            (x, y, z) position for the object center
        """

        # Ensure minimum size
        object_size = self.physics.ensure_minimum_size(object_size)

        # Get existing objects for collision detection
        existing_bboxes = self._get_existing_bounding_boxes(exclude_id=object_id)

        if placement_type == "on_top_of" and target_id:
            return self._place_on_surface(object_size, target_id, existing_bboxes, randomness)

        elif placement_type == "near" and target_id:
            return self._place_near_target(object_size, target_id, existing_bboxes, randomness)

        elif placement_type == "ground":
            return self._place_on_ground(object_size, existing_bboxes, randomness)

        else:  # "random" or fallback
            return self._place_randomly(object_size, existing_bboxes)

    def validate_and_adjust_position(self, position: Tuple[float, float, float],
                                   object_size: Tuple[float, float, float],
                                   object_id: str) -> Tuple[float, float, float]:
        """
        Validate and adjust an LLM-calculated position using physics rules.

        Args:
            position: LLM-calculated position (x, y, z)
            object_size: (width, depth, height) of the object
            object_id: ID of the object being placed

        Returns:
            Validated and adjusted position
        """

        # Ensure minimum size
        object_size = self.physics.ensure_minimum_size(object_size)

        # First, validate the position using physics rules (ground level, etc.)
        validated_position = self.physics.validate_object_position(
            position=position,
            size=object_size,
            allow_stacking=True
        )

        # Use advanced collision detection to find safe position
        from .collision_detector import collision_detector

        # Update collision detector with current scene state
        self._sync_collision_detector(exclude_id=object_id)

        # Try to find a safe position near the validated position
        safe_position = collision_detector.find_safe_position(
            object_size=object_size,
            preferred_position=validated_position,
            search_radius=0.8,  # Search within 80cm radius
            max_attempts=15
        )

        if safe_position:
            return safe_position
        else:
            # If no safe position found, fall back to ground placement
            # This uses the existing collision avoidance logic
            existing_bboxes = self._get_existing_bounding_boxes(exclude_id=object_id)
            return self._place_on_ground(object_size, existing_bboxes, randomness=0.5)

    def _place_on_surface(self, object_size: Tuple[float, float, float], target_id: str,
                         existing_bboxes: List[BoundingBox], randomness: float) -> Tuple[float, float, float]:
        """Place object on top of target object's surface."""

        if target_id not in self.graph.nodes:
            # Fallback to ground placement
            return self._place_on_ground(object_size, existing_bboxes, randomness)

        target_node = self.graph.nodes[target_id]
        target_size = target_node.bbox['xyz']
        target_bbox = BoundingBox(target_node.pos, target_size)

        # Try multiple positions on the surface to avoid collisions
        max_attempts = 10
        for attempt in range(max_attempts):
            # Random offset within the target surface (but not too close to edges)
            max_offset = min(target_size[0], target_size[1]) * 0.3  # Stay within 30% of surface
            offset_x = random.uniform(-max_offset, max_offset) * randomness
            offset_y = random.uniform(-max_offset, max_offset) * randomness

            position = self.physics.place_on_surface(target_bbox, object_size, (offset_x, offset_y))
            candidate_bbox = BoundingBox(position, object_size)

            # Check for collisions (excluding the target surface itself)
            collision_found = False
            for existing_bbox in existing_bboxes:
                if existing_bbox.center != target_bbox.center:  # Don't check against target
                    if self.physics.check_collision(candidate_bbox, existing_bbox):
                        collision_found = True
                        break

            if not collision_found:
                return position

        # If no collision-free position found, place at center of target surface
        return self.physics.place_on_surface(target_bbox, object_size)

    def _place_near_target(self, object_size: Tuple[float, float, float], target_id: str,
                          existing_bboxes: List[BoundingBox], randomness: float) -> Tuple[float, float, float]:
        """Place object near target on the ground."""

        if target_id not in self.graph.nodes:
            return self._place_on_ground(object_size, existing_bboxes, randomness)

        target_node = self.graph.nodes[target_id]
        target_pos = target_node.pos

        # Try to find a safe position near the target
        min_distance = 0.3 + max(object_size) / 2  # Ensure some clearance
        max_distance = 0.8

        position = self.physics.find_safe_placement(
            target_pos, object_size, existing_bboxes,
            min_distance=min_distance, max_attempts=15
        )

        if position:
            # Add some randomness if requested
            if randomness > 0:
                angle_offset = random.uniform(-math.pi/4, math.pi/4) * randomness
                distance_offset = random.uniform(-0.1, 0.1) * randomness

                current_angle = math.atan2(position[1] - target_pos[1], position[0] - target_pos[0])
                new_angle = current_angle + angle_offset
                current_distance = self.physics.distance_3d(position[:2] + (0,), target_pos[:2] + (0,))
                new_distance = max(min_distance, current_distance + distance_offset)

                position = self.physics.place_near_ground(target_pos, object_size, new_distance, new_angle)

            return position

        # Fallback to ground placement if no safe position found
        return self._place_on_ground(object_size, existing_bboxes, randomness)

    def _place_on_ground(self, object_size: Tuple[float, float, float],
                        existing_bboxes: List[BoundingBox], randomness: float) -> Tuple[float, float, float]:
        """Place object on the ground in a safe location."""

        # Define scene boundaries
        scene_bounds = {
            'x_min': 0.5, 'x_max': 4.5,
            'y_min': 0.5, 'y_max': 2.5
        }

        # Try multiple random positions
        max_attempts = 25
        for attempt in range(max_attempts):
            x = random.uniform(scene_bounds['x_min'], scene_bounds['x_max'])
            y = random.uniform(scene_bounds['y_min'], scene_bounds['y_max'])

            position = self.physics.align_to_ground((x, y, 0), object_size)
            candidate_bbox = BoundingBox(position, object_size)

            # Check for collisions
            collision_found = False
            for existing_bbox in existing_bboxes:
                if self.physics.check_collision(candidate_bbox, existing_bbox):
                    collision_found = True
                    break

            if not collision_found:
                return position

        # Fallback: place at a default safe location
        default_x = scene_bounds['x_min'] + 0.5
        default_y = scene_bounds['y_min'] + 0.5
        return self.physics.align_to_ground((default_x, default_y, 0), object_size)

    def _place_randomly(self, object_size: Tuple[float, float, float],
                       existing_bboxes: List[BoundingBox]) -> Tuple[float, float, float]:
        """Place object randomly in the scene."""
        return self._place_on_ground(object_size, existing_bboxes, randomness=1.0)

    def _get_existing_bounding_boxes(self, exclude_id: Optional[str] = None) -> List[BoundingBox]:
        """Get bounding boxes of all existing objects in the scene."""
        bboxes = []

        for node_id, node in self.graph.nodes.items():
            if exclude_id and node_id == exclude_id:
                continue

            size = self.physics.ensure_minimum_size(node.bbox['xyz'])
            # Validate position to ensure it's properly grounded
            position = self.physics.validate_object_position(node.pos, size)

            bboxes.append(BoundingBox(position, size))

        return bboxes

    def validate_all_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """Validate and correct positions of all objects in the scene."""
        corrections = {}

        for node_id, node in self.graph.nodes.items():
            size = self.physics.ensure_minimum_size(node.bbox['xyz'])
            # Check if object has proper support
            corrected_pos = self._validate_with_support_check(node.pos, size, node_id)

            # If position was corrected, record it
            if corrected_pos != node.pos:
                corrections[node_id] = corrected_pos

        return corrections

    def force_ground_alignment(self) -> Dict[str, Tuple[float, float, float]]:
        """Force ALL objects to be aligned to ground, regardless of current position."""
        corrections = {}

        for node_id, node in self.graph.nodes.items():
            size = self.physics.ensure_minimum_size(node.bbox['xyz'])
            # Force ground alignment for ALL objects
            ground_aligned_pos = self.physics.align_to_ground(node.pos, size)

            # Always record the correction (even if position unchanged)
            corrections[node_id] = ground_aligned_pos

        return corrections

    def get_object_ground_clearance(self, object_id: str) -> float:
        """Get how far above ground an object is positioned."""
        if object_id not in self.graph.nodes:
            return 0.0

        node = self.graph.nodes[object_id]
        size = self.physics.ensure_minimum_size(node.bbox['xyz'])
        bbox = BoundingBox(node.pos, size)

        return bbox.ground_level - self.physics.GROUND_LEVEL

    def _validate_with_support_check(self, position: Tuple[float, float, float],
                                   size: Tuple[float, float, float], object_id: str) -> Tuple[float, float, float]:
        """Validate object position with support surface checking."""
        size = self.physics.ensure_minimum_size(size)
        ground_z = self.physics.GROUND_LEVEL + size[2]/2

        # If object is at or near ground level, it's fine
        if abs(position[2] - ground_z) < 0.05:
            return position

        # If object is above ground, check if it has support
        if position[2] > ground_z:
            object_bbox = BoundingBox(position, size)

            # Look for supporting objects below this one
            for other_id, other_node in self.graph.nodes.items():
                if other_id == object_id:
                    continue

                other_size = self.physics.ensure_minimum_size(other_node.bbox['xyz'])
                other_bbox = BoundingBox(other_node.pos, other_size)

                # Check if this object is roughly above the other object
                if (abs(object_bbox.center[0] - other_bbox.center[0]) < other_size[0]/2 + 0.1 and
                    abs(object_bbox.center[1] - other_bbox.center[1]) < other_size[1]/2 + 0.1):

                    # Check if object is sitting on top of the other object
                    expected_z = other_bbox.top_level + size[2]/2
                    if abs(position[2] - expected_z) < 0.1:
                        # Object is properly supported
                        return position

            # Object is floating without support - bring it to ground
            return (position[0], position[1], ground_z)

        # Object is below ground - fix it
        if position[2] < ground_z:
            return (position[0], position[1], ground_z)

        return position

    def _sync_collision_detector(self, exclude_id: Optional[str] = None):
        """Sync the global collision detector with current scene state."""
        from .collision_detector import collision_detector

        # Clear existing collision boxes
        collision_detector.collision_boxes.clear()

        # Add all current objects to collision detector
        for node_id, node in self.graph.nodes.items():
            if exclude_id and node_id == exclude_id:
                continue

            size = self.physics.ensure_minimum_size(node.bbox['xyz'])
            # Use validated position to ensure proper grounding
            position = self.physics.validate_object_position(node.pos, size)

            collision_detector.add_object(node_id, position, size)

    def get_collision_report(self) -> str:
        """Get a detailed collision report for debugging."""
        from .collision_detector import collision_detector

        self._sync_collision_detector()
        info = collision_detector.get_collision_info()
        layout = collision_detector.visualize_2d_layout()

        report = [
            "=== Collision Detection Report ===",
            f"Total objects: {info['total_objects']}",
            f"Collision pairs: {info['collision_count']}",
        ]

        if info['collision_pairs']:
            report.append("Colliding objects:")
            for obj1, obj2 in info['collision_pairs']:
                report.append(f"  - {obj1} ↔ {obj2}")

        report.append("")
        report.append(layout)

        return "\n".join(report)
