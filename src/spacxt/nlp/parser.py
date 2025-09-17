"""
Natural Language Command Parser for SpacXT.

Parses natural language commands into structured actions that can modify the spatial scene.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    """Structured representation of a parsed natural language command."""
    action: str  # "add", "move", "remove", "place"
    object_type: str  # "coffee_cup", "book", "lamp", etc.
    object_id: Optional[str] = None  # Generated if not specified
    target_object: Optional[str] = None  # "table", "chair", etc.
    spatial_relation: Optional[str] = None  # "on", "near", "beside", etc.
    position: Optional[Tuple[float, float, float]] = None
    properties: Dict[str, Any] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class CommandParser:
    """Natural language command parser for spatial scene modifications."""

    def __init__(self):
        # Object type mappings
        self.object_synonyms = {
            # Containers and dishes
            'cup': 'coffee_cup', 'coffee_cup': 'coffee_cup', 'mug': 'coffee_cup',
            'glass': 'glass', 'wine_glass': 'wine_glass',
            'plate': 'plate', 'dish': 'plate',
            'bowl': 'bowl',

            # Books and media
            'book': 'book', 'novel': 'book', 'magazine': 'magazine',
            'laptop': 'laptop', 'computer': 'laptop',
            'phone': 'phone', 'smartphone': 'phone',

            # Decorative items
            'lamp': 'lamp', 'light': 'lamp',
            'vase': 'vase', 'flower': 'vase',
            'candle': 'candle',

            # Food items
            'apple': 'apple', 'fruit': 'apple',
            'bottle': 'bottle', 'water_bottle': 'bottle',

            # Office items
            'pen': 'pen', 'pencil': 'pen',
            'paper': 'paper', 'document': 'paper',
            'folder': 'folder',
        }

        # Action patterns
        self.action_patterns = [
            # Place/Put patterns
            (r'(?:put|place|set)\s+(?:a\s+|an\s+|the\s+)?(\w+)(?:\s+\w+)?\s+(?:on|onto|upon)\s+(?:the\s+)?(\w+)', 'place_on'),
            (r'(?:put|place|set)\s+(?:a\s+|an\s+|the\s+)?(\w+)(?:\s+\w+)?\s+(?:near|beside|next\s+to)\s+(?:the\s+)?(\w+)', 'place_near'),
            (r'(?:add|create)\s+(?:a\s+|an\s+)?(\w+)(?:\s+\w+)?(?:\s+(?:on|to|near)\s+(?:the\s+)?(\w+))?', 'add'),

            # Move patterns
            (r'(?:move|shift)\s+(?:the\s+)?(\w+)\s+(?:to|onto|near)\s+(?:the\s+)?(\w+)', 'move_to'),
            (r'(?:move|shift)\s+(?:the\s+)?(\w+)\s+(?:away\s+from|from)\s+(?:the\s+)?(\w+)', 'move_away'),

            # Remove patterns
            (r'(?:remove|delete|take\s+away)\s+(?:the\s+)?(\w+)', 'remove'),
        ]

        # Spatial relation mappings
        self.spatial_relations = {
            'on': 'on_top_of',
            'onto': 'on_top_of',
            'upon': 'on_top_of',
            'near': 'near',
            'beside': 'near',
            'next_to': 'near',
            'close_to': 'near',
        }

        # Object counters for unique IDs
        self.object_counters = {}

    def parse(self, command: str) -> Optional[ParsedCommand]:
        """Parse a natural language command into a structured representation."""
        command = command.lower().strip()

        # Try each action pattern
        for pattern, action_type in self.action_patterns:
            match = re.search(pattern, command)
            if match:
                return self._parse_match(match, action_type, command)

        return None

    def _parse_match(self, match: re.Match, action_type: str, original_command: str) -> ParsedCommand:
        """Parse a regex match into a ParsedCommand."""
        groups = match.groups()

        # Extract object type
        object_word = groups[0] if groups else None
        object_type = self._normalize_object_type(object_word)

        # Generate unique object ID
        object_id = self._generate_object_id(object_type)

        # Extract target object
        target_object = groups[1] if len(groups) > 1 and groups[1] else None

        # Determine action and spatial relation
        if action_type == 'place_on':
            action = 'add'
            spatial_relation = 'on_top_of'
        elif action_type == 'place_near':
            action = 'add'
            spatial_relation = 'near'
        elif action_type == 'add':
            action = 'add'
            spatial_relation = 'near' if target_object else None
        elif action_type.startswith('move_'):
            action = 'move'
            spatial_relation = 'near' if action_type == 'move_to' else 'far'
            # For move commands, the first group is the object to move
            object_id = object_word  # Use as existing object reference
        elif action_type == 'remove':
            action = 'remove'
            object_id = object_word  # Use as existing object reference
            spatial_relation = None
        else:
            action = 'add'
            spatial_relation = None

        return ParsedCommand(
            action=action,
            object_type=object_type,
            object_id=object_id,
            target_object=target_object,
            spatial_relation=spatial_relation,
            properties={'command': original_command}
        )

    def _normalize_object_type(self, word: str) -> str:
        """Normalize object word to standard object type."""
        if not word:
            return 'unknown_object'

        # Remove common prefixes/suffixes
        word = re.sub(r'^(a|an|the)\s+', '', word)
        word = re.sub(r's$', '', word)  # Remove plural

        return self.object_synonyms.get(word, word)

    def _generate_object_id(self, object_type: str) -> str:
        """Generate a unique ID for an object type."""
        if object_type not in self.object_counters:
            self.object_counters[object_type] = 0

        self.object_counters[object_type] += 1
        return f"{object_type}_{self.object_counters[object_type]}"


# Example usage and testing
if __name__ == "__main__":
    parser = CommandParser()

    test_commands = [
        "put a coffee cup on the table",
        "place a book near the chair",
        "add a lamp",
        "move the chair to the stove",
        "remove the cup",
        "set a wine glass onto the table",
        "put an apple beside the laptop"
    ]

    print("Testing Command Parser:")
    print("=" * 40)

    for cmd in test_commands:
        result = parser.parse(cmd)
        print(f"Command: '{cmd}'")
        if result:
            print(f"  Action: {result.action}")
            print(f"  Object: {result.object_type} (ID: {result.object_id})")
            print(f"  Target: {result.target_object}")
            print(f"  Relation: {result.spatial_relation}")
        else:
            print("  ❌ Could not parse")
        print()
