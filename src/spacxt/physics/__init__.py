"""
Physics system for SpacXT - handles object positioning, collision detection, and ground alignment.
"""

from .placement_engine import PlacementEngine
from .physics_utils import PhysicsUtils

__all__ = ["PlacementEngine", "PhysicsUtils"]
