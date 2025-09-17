"""
Physics utilities for spatial object placement and collision detection.
"""

import math
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """3D bounding box representation."""
    center: Tuple[float, float, float]
    size: Tuple[float, float, float]  # width, depth, height

    @property
    def min_point(self) -> Tuple[float, float, float]:
        """Get minimum corner of bounding box."""
        return (
            self.center[0] - self.size[0]/2,
            self.center[1] - self.size[1]/2,
            self.center[2] - self.size[2]/2
        )

    @property
    def max_point(self) -> Tuple[float, float, float]:
        """Get maximum corner of bounding box."""
        return (
            self.center[0] + self.size[0]/2,
            self.center[1] + self.size[1]/2,
            self.center[2] + self.size[2]/2
        )

    @property
    def ground_level(self) -> float:
        """Get the Z coordinate where this object touches the ground."""
        return self.center[2] - self.size[2]/2

    @property
    def top_level(self) -> float:
        """Get the Z coordinate of the top of this object."""
        return self.center[2] + self.size[2]/2


class PhysicsUtils:
    """Utility functions for physics-based object placement."""

    GROUND_LEVEL = 0.0
    MIN_OBJECT_SIZE = 0.01  # Minimum size to prevent flat objects
    PLACEMENT_TOLERANCE = 0.001  # Small gap for floating point precision

    @staticmethod
    def ensure_minimum_size(size: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Ensure object has minimum size in all dimensions."""
        return tuple(max(dim, PhysicsUtils.MIN_OBJECT_SIZE) for dim in size)

    @staticmethod
    def align_to_ground(center: Tuple[float, float, float], size: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Align object center so it sits properly on the ground."""
        size = PhysicsUtils.ensure_minimum_size(size)
        return (center[0], center[1], PhysicsUtils.GROUND_LEVEL + size[2]/2)

    @staticmethod
    def place_on_surface(target_bbox: BoundingBox, object_size: Tuple[float, float, float],
                        offset: Tuple[float, float] = (0, 0)) -> Tuple[float, float, float]:
        """Place object on top of target object's surface."""
        object_size = PhysicsUtils.ensure_minimum_size(object_size)

        return (
            target_bbox.center[0] + offset[0],
            target_bbox.center[1] + offset[1],
            target_bbox.top_level + object_size[2]/2 + PhysicsUtils.PLACEMENT_TOLERANCE
        )

    @staticmethod
    def place_near_ground(target_center: Tuple[float, float, float], object_size: Tuple[float, float, float],
                         distance: float, angle: float) -> Tuple[float, float, float]:
        """Place object near target on the ground."""
        object_size = PhysicsUtils.ensure_minimum_size(object_size)

        # Calculate position near target
        x = target_center[0] + distance * math.cos(angle)
        y = target_center[1] + distance * math.sin(angle)
        z = PhysicsUtils.GROUND_LEVEL + object_size[2]/2

        return (x, y, z)

    @staticmethod
    def check_collision(bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        """Check if two bounding boxes collide (overlap)."""
        min1, max1 = bbox1.min_point, bbox1.max_point
        min2, max2 = bbox2.min_point, bbox2.max_point

        # Check for separation along each axis
        if (max1[0] <= min2[0] or max2[0] <= min1[0] or
            max1[1] <= min2[1] or max2[1] <= min1[1] or
            max1[2] <= min2[2] or max2[2] <= min1[2]):
            return False

        return True

    @staticmethod
    def distance_3d(pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]) -> float:
        """Calculate 3D Euclidean distance between two points."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))

    @staticmethod
    def find_safe_placement(target_pos: Tuple[float, float, float], object_size: Tuple[float, float, float],
                           existing_objects: List[BoundingBox], min_distance: float = 0.1,
                           max_attempts: int = 20) -> Optional[Tuple[float, float, float]]:
        """Find a safe placement position that doesn't collide with existing objects."""
        object_size = PhysicsUtils.ensure_minimum_size(object_size)

        for attempt in range(max_attempts):
            # Try different angles around the target
            angle = (attempt * 2 * math.pi) / max_attempts
            distance = min_distance + (attempt * 0.1)  # Gradually increase distance

            candidate_pos = PhysicsUtils.place_near_ground(target_pos, object_size, distance, angle)
            candidate_bbox = BoundingBox(candidate_pos, object_size)

            # Check for collisions with existing objects
            collision_found = False
            for existing_bbox in existing_objects:
                if PhysicsUtils.check_collision(candidate_bbox, existing_bbox):
                    collision_found = True
                    break

            if not collision_found:
                return candidate_pos

        # If no safe position found, return a fallback position
        return PhysicsUtils.align_to_ground(target_pos, object_size)

    @staticmethod
    def validate_object_position(position: Tuple[float, float, float], size: Tuple[float, float, float],
                                allow_stacking: bool = True) -> Tuple[float, float, float]:
        """Validate and correct object position to ensure it's properly supported."""
        size = PhysicsUtils.ensure_minimum_size(size)

        # Calculate minimum valid Z (sitting on ground)
        ground_z = PhysicsUtils.GROUND_LEVEL + size[2]/2

        if not allow_stacking:
            # Force to ground level
            return (position[0], position[1], ground_z)

        # Allow objects above ground level if they're reasonably positioned
        # Only correct if object is below ground or floating unreasonably high
        if position[2] < ground_z:
            # Object is below ground - fix it
            return (position[0], position[1], ground_z)
        elif position[2] > ground_z + 2.0:  # More than 2 meters above ground
            # Object is floating too high - bring it down
            return (position[0], position[1], ground_z)
        else:
            # Object is at reasonable height - probably stacked on something
            return position

    @staticmethod
    def get_support_surface_height(object_bbox: BoundingBox) -> float:
        """Get the height of the surface that can support other objects."""
        return object_bbox.top_level
