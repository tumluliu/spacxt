"""
Physics system for SpacXT - handles object positioning, collision detection, and ground alignment.
"""

from .placement_engine import PlacementEngine
from .physics_utils import PhysicsUtils
from .support_system import SupportSystem
from .collision_detector import CollisionDetector

__all__ = ["PlacementEngine", "PhysicsUtils", "SupportSystem", "CollisionDetector"]
