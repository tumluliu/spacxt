"""
LLM-powered Natural Language Command Parser for SpacXT.

Uses Large Language Models via OpenRouter to parse complex spatial commands.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .llm_client import LLMClient


@dataclass
class ParsedCommand:
    """Structured representation of a parsed natural language command."""
    action: str  # "add", "move", "remove", "modify"
    object_type: str  # "coffee_cup", "book", "lamp", etc.
    object_id: Optional[str] = None  # Generated or existing ID
    target_object: Optional[str] = None  # "table", "chair", etc.
    spatial_relation: Optional[str] = None  # "on_top_of", "near", "custom"
    position: Optional[Tuple[float, float, float]] = None  # LLM-calculated position for custom relations
    properties: Dict[str, Any] = None
    confidence: float = 0.0
    quantity: int = 1  # Number of objects to add/modify

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class LLMCommandParser:
    """LLM-powered natural language command parser for spatial scene modifications."""

    def __init__(self):
        try:
            self.llm_client = LLMClient()
            self.llm_available = True
        except Exception as e:
            print(f"⚠️  LLM client initialization failed: {e}")
            print("   Falling back to rule-based parsing")
            self.llm_available = False
            self._init_fallback_parser()

        # Object counters for unique IDs
        self.object_counters = {}

    def _init_fallback_parser(self):
        """Initialize fallback rule-based parser."""
        import re

        # Basic object synonyms for fallback
        self.object_synonyms = {
            'cup': 'coffee_cup', 'coffee_cup': 'coffee_cup', 'mug': 'coffee_cup',
            'book': 'book', 'laptop': 'laptop', 'phone': 'phone',
            'lamp': 'lamp', 'bottle': 'bottle', 'pen': 'pen'
        }

        # Simple action patterns for fallback
        self.action_patterns = [
            (r'(?:put|place|set)\s+(?:a\s+|an\s+|the\s+)?(\w+)(?:\s+\w+)?\s+(?:on|onto|upon)\s+(?:the\s+)?(\w+)', 'place_on'),
            (r'(?:put|place|set)\s+(?:a\s+|an\s+|the\s+)?(\w+)(?:\s+\w+)?\s+(?:near|beside)\s+(?:the\s+)?(\w+)', 'place_near'),
            (r'(?:add|create)\s+(?:a\s+|an\s+)?(\w+)', 'add'),
            (r'(?:move)\s+(?:the\s+)?(\w+)\s+(?:closer\s+to|nearer\s+to|near)\s+(?:the\s+)?(\w+)', 'move_near'),
            (r'(?:move)\s+(?:the\s+)?(\w+)\s+(?:to|onto)\s+(?:the\s+)?(\w+)', 'move_to'),
            (r'(?:remove|delete)\s+(?:the\s+)?(\w+)', 'remove'),
        ]

    def parse(self, command: str, scene_context: Dict[str, Any] = None) -> Optional[ParsedCommand]:
        """Parse a natural language command into a structured representation."""

        if self.llm_available:
            return self._parse_with_llm(command, scene_context or {})
        else:
            return self._parse_with_rules(command)

    def _parse_with_llm(self, command: str, scene_context: Dict[str, Any]) -> Optional[ParsedCommand]:
        """Parse command using LLM."""
        try:
            # Get LLM parsing result
            llm_result = self.llm_client.parse_spatial_command(command, scene_context)

            if not llm_result:
                print(f"❌ LLM failed to parse: {command}")
                return None

            # Convert LLM result to ParsedCommand
            quantity = llm_result.get("quantity", 1)
            print(f"🔢 LLM parsed quantity: {quantity} for command: '{command}'")
            print(f"📝 Full LLM result: {llm_result}")

            parsed_cmd = ParsedCommand(
                action=llm_result.get("action", "add"),
                object_type=llm_result.get("object_type", "unknown_object"),
                object_id=llm_result.get("object_id"),
                target_object=llm_result.get("target_object"),
                spatial_relation=llm_result.get("spatial_relation"),
                position=tuple(llm_result["position"]) if llm_result.get("position") else None,
                properties=llm_result.get("properties", {}),
                confidence=llm_result.get("confidence", 0.8),
                quantity=quantity
            )

            # Generate object ID if not provided and action is add
            if parsed_cmd.action == "add" and not parsed_cmd.object_id:
                parsed_cmd.object_id = self._generate_object_id(parsed_cmd.object_type)

            # Enhance object properties with LLM if adding new object
            if parsed_cmd.action == "add":
                enhanced_props = self.llm_client.enhance_object_properties(parsed_cmd.object_type)
                parsed_cmd.properties.update(enhanced_props)

            return parsed_cmd

        except Exception as e:
            print(f"❌ LLM parsing error: {e}")
            return None

    def _parse_with_rules(self, command: str) -> Optional[ParsedCommand]:
        """Fallback rule-based parsing."""
        import re

        command = command.lower().strip()

        # Try each action pattern
        for pattern, action_type in self.action_patterns:
            match = re.search(pattern, command)
            if match:
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
                    spatial_relation = None
                elif action_type in ['move_to', 'move_near']:
                    action = 'move'
                    spatial_relation = 'near'
                    object_id = object_word  # Use as existing object reference
                elif action_type == 'remove':
                    action = 'remove'
                    object_id = object_word  # Use as existing object reference
                    spatial_relation = None
                else:
                    action = 'add'
                    spatial_relation = None

                # Extract quantity from rule-based parsing
                quantity = self._extract_quantity_from_command(command)

                return ParsedCommand(
                    action=action,
                    object_type=object_type,
                    object_id=object_id,
                    target_object=target_object,
                    spatial_relation=spatial_relation,
                    properties={'command': command},
                    confidence=0.7,  # Lower confidence for rule-based
                    quantity=quantity
                )

        return None

    def _normalize_object_type(self, word: str) -> str:
        """Normalize object word to standard object type."""
        if not word:
            return 'unknown_object'

        # Remove common prefixes/suffixes
        import re
        word = re.sub(r'^(a|an|the)\s+', '', word)
        word = re.sub(r's$', '', word)  # Remove plural

        return self.object_synonyms.get(word, word)

    def _extract_quantity_from_command(self, command: str) -> int:
        """Extract quantity from command text (rule-based fallback)."""
        import re

        # Number words to digits mapping
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'a': 1, 'an': 1, 'couple': 2, 'few': 3, 'several': 3,
            'some': 2, 'many': 5, 'multiple': 3
        }

        command_lower = command.lower()

        # Look for explicit numbers first
        number_match = re.search(r'\b(\d+)\b', command_lower)
        if number_match:
            return int(number_match.group(1))

        # Look for number words
        for word, value in number_words.items():
            if re.search(rf'\b{word}\b', command_lower):
                return value

        return 1  # Default to single object

    def _generate_object_id(self, object_type: str) -> str:
        """Generate a unique ID for an object type."""
        if object_type not in self.object_counters:
            self.object_counters[object_type] = 0

        self.object_counters[object_type] += 1
        return f"{object_type}_{self.object_counters[object_type]}"


# Example usage and testing
if __name__ == "__main__":
    parser = LLMCommandParser()

    test_commands = [
        "put a coffee cup on the table",
        "place a book near the chair",
        "add a modern laptop to the scene",
        "move the chair closer to the stove",
        "remove the cup from the table",
        "set a wine glass elegantly on the dining table",
        "place a small potted plant beside the window"
    ]

    print("Testing LLM Command Parser:")
    print("=" * 50)

    # Mock scene context
    scene_context = {
        "objects": {
            "table_1": type('Node', (), {'cls': 'table', 'pos': (2.0, 1.5, 0.4)})(),
            "chair_12": type('Node', (), {'cls': 'chair', 'pos': (1.8, 1.2, 0.45)})(),
            "stove": type('Node', (), {'cls': 'stove', 'pos': (3.5, 0.5, 0.5)})()
        }
    }

    for cmd in test_commands:
        result = parser.parse(cmd, scene_context)
        print(f"Command: '{cmd}'")
        if result:
            print(f"  Action: {result.action}")
            print(f"  Object: {result.object_type} (ID: {result.object_id})")
            print(f"  Target: {result.target_object}")
            print(f"  Relation: {result.spatial_relation}")
            print(f"  Confidence: {result.confidence:.2f}")
        else:
            print("  ❌ Could not parse")
        print()
