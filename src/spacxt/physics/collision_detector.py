"""
Collision Detection for SpacXT - using Shapely for geometric collision detection.

This module provides collision detection capabilities that can be easily migrated
to Rust using rapier3d/parry3d crates in the future.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import Polygon, Point
from shapely.affinity import translate
from dataclasses import dataclass


@dataclass
class CollisionBox:
    """3D bounding box for collision detection."""
    center: Tuple[float, float, float]  # (x, y, z)
    size: Tuple[float, float, float]    # (width, depth, height)
    id: str = ""

    @property
    def min_point(self) -> Tuple[float, float, float]:
        """Get minimum corner of the box."""
        return (
            self.center[0] - self.size[0] / 2,
            self.center[1] - self.size[1] / 2,
            self.center[2] - self.size[2] / 2
        )

    @property
    def max_point(self) -> Tuple[float, float, float]:
        """Get maximum corner of the box."""
        return (
            self.center[0] + self.size[0] / 2,
            self.center[1] + self.size[1] / 2,
            self.center[2] + self.size[2] / 2
        )

    def to_2d_polygon(self) -> Polygon:
        """Convert to 2D polygon for collision detection (ignoring Z)."""
        min_x, min_y, _ = self.min_point
        max_x, max_y, _ = self.max_point

        # Create rectangle in 2D (X-Y plane)
        return Polygon([
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y)
        ])

    def overlaps_3d(self, other: 'CollisionBox') -> bool:
        """Check if this box overlaps with another box in 3D."""
        # Check overlap in all three dimensions
        min1, max1 = self.min_point, self.max_point
        min2, max2 = other.min_point, other.max_point

        # Boxes overlap if they overlap in ALL dimensions
        x_overlap = max1[0] > min2[0] and min1[0] < max2[0]
        y_overlap = max1[1] > min2[1] and min1[1] < max2[1]
        z_overlap = max1[2] > min2[2] and min1[2] < max2[2]

        return x_overlap and y_overlap and z_overlap

    def distance_to(self, other: 'CollisionBox') -> float:
        """Calculate distance between box centers."""
        dx = self.center[0] - other.center[0]
        dy = self.center[1] - other.center[1]
        dz = self.center[2] - other.center[2]
        return np.sqrt(dx*dx + dy*dy + dz*dz)


class CollisionDetector:
    """Advanced collision detection system using Shapely."""

    def __init__(self):
        self.collision_boxes: Dict[str, CollisionBox] = {}
        self.collision_margin = 0.05  # 5cm safety margin

    def add_object(self, object_id: str, center: Tuple[float, float, float],
                   size: Tuple[float, float, float]):
        """Add an object to the collision detection system."""
        self.collision_boxes[object_id] = CollisionBox(center, size, object_id)

    def remove_object(self, object_id: str):
        """Remove an object from collision detection."""
        if object_id in self.collision_boxes:
            del self.collision_boxes[object_id]

    def update_object_position(self, object_id: str, new_center: Tuple[float, float, float]):
        """Update an object's position."""
        if object_id in self.collision_boxes:
            box = self.collision_boxes[object_id]
            self.collision_boxes[object_id] = CollisionBox(new_center, box.size, object_id)

    def check_collision(self, box1: CollisionBox, box2: CollisionBox,
                       use_margin: bool = True) -> bool:
        """Check if two collision boxes overlap."""
        if use_margin:
            # Expand boxes by collision margin for safety
            expanded_size1 = (
                box1.size[0] + 2 * self.collision_margin,
                box1.size[1] + 2 * self.collision_margin,
                box1.size[2] + 2 * self.collision_margin
            )
            expanded_box1 = CollisionBox(box1.center, expanded_size1)
            return expanded_box1.overlaps_3d(box2)
        else:
            return box1.overlaps_3d(box2)

    def check_collision_at_position(self, object_id: str, position: Tuple[float, float, float],
                                   size: Tuple[float, float, float]) -> List[str]:
        """
        Check what objects would collide if object_id was placed at position.

        Returns:
            List of object IDs that would collide
        """
        test_box = CollisionBox(position, size, object_id)
        collisions = []

        for other_id, other_box in self.collision_boxes.items():
            if other_id != object_id:  # Don't check collision with self
                if self.check_collision(test_box, other_box):
                    collisions.append(other_id)

        return collisions

    def find_safe_position(self, object_size: Tuple[float, float, float],
                          preferred_position: Tuple[float, float, float],
                          search_radius: float = 1.0,
                          max_attempts: int = 20) -> Optional[Tuple[float, float, float]]:
        """
        Find a safe position near the preferred position.

        Args:
            object_size: Size of the object to place
            preferred_position: Desired position
            search_radius: How far to search around preferred position
            max_attempts: Maximum number of positions to try

        Returns:
            Safe position or None if no safe position found
        """

        # First check if preferred position is already safe and properly grounded
        ground_z = 0.0 + object_size[2]/2  # GROUND_LEVEL + half height
        grounded_preferred = (preferred_position[0], preferred_position[1], ground_z)

        if not self.check_collision_at_position("temp", grounded_preferred, object_size):
            return grounded_preferred

        # Try positions in expanding circles around preferred position
        for attempt in range(max_attempts):
            # Generate random position within search radius
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.uniform(0, search_radius * (1 + attempt / max_attempts))

            offset_x = distance * np.cos(angle)
            offset_y = distance * np.sin(angle)

            # Calculate proper ground level for this object size
            ground_z = 0.0 + object_size[2]/2  # GROUND_LEVEL + half height

            test_position = (
                preferred_position[0] + offset_x,
                preferred_position[1] + offset_y,
                ground_z  # Ensure proper grounding
            )

            # Check if this position is collision-free
            if not self.check_collision_at_position("temp", test_position, object_size):
                return test_position

        return None  # No safe position found

    def get_collision_info(self) -> Dict[str, Any]:
        """Get information about current collision state."""
        total_objects = len(self.collision_boxes)
        collisions = []

        # Check all pairs for collisions
        box_items = list(self.collision_boxes.items())
        for i in range(len(box_items)):
            for j in range(i + 1, len(box_items)):
                id1, box1 = box_items[i]
                id2, box2 = box_items[j]

                if self.check_collision(box1, box2, use_margin=False):
                    collisions.append((id1, id2))

        return {
            "total_objects": total_objects,
            "collision_pairs": collisions,
            "collision_count": len(collisions)
        }

    def visualize_2d_layout(self) -> str:
        """Generate a simple ASCII visualization of the 2D layout."""
        if not self.collision_boxes:
            return "No objects in collision detector"

        # Find bounds
        all_boxes = list(self.collision_boxes.values())
        min_x = min(box.min_point[0] for box in all_boxes) - 0.5
        max_x = max(box.max_point[0] for box in all_boxes) + 0.5
        min_y = min(box.min_point[1] for box in all_boxes) - 0.5
        max_y = max(box.max_point[1] for box in all_boxes) + 0.5

        layout_info = []
        layout_info.append(f"2D Layout ({min_x:.1f},{min_y:.1f}) to ({max_x:.1f},{max_y:.1f}):")

        for obj_id, box in self.collision_boxes.items():
            center = box.center
            size = box.size
            layout_info.append(f"  {obj_id}: center=({center[0]:.2f},{center[1]:.2f},{center[2]:.2f}) size=({size[0]:.2f}x{size[1]:.2f}x{size[2]:.2f})")

        return "\n".join(layout_info)


# Global collision detector instance
collision_detector = CollisionDetector()
