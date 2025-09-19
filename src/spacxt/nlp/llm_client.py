"""
LLM Client for OpenRouter API integration.
"""

import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient:
    """Client for interacting with LLMs via OpenRouter."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

        # Conversation context tracking
        self.conversation_history = []  # Store recent commands and results
        self.max_history_length = 10   # Keep last 10 interactions

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment variables. "
                "Please add it to your .env file."
            )

        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def add_to_conversation_history(self, command: str, result: Dict[str, Any], success: bool):
        """Add a command and its result to conversation history."""
        self.conversation_history.append({
            "command": command,
            "result": result,
            "success": success,
            "timestamp": len(self.conversation_history) + 1
        })

        # Keep only recent history
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]

    def get_conversation_context(self) -> str:
        """Build conversation context string for the LLM."""
        if not self.conversation_history:
            return "No previous commands in this conversation."

        context_lines = ["Recent conversation history:"]
        for i, entry in enumerate(self.conversation_history[-5:], 1):  # Last 5 commands
            if entry["success"] and entry["result"]:
                action = entry["result"].get("action", "unknown")
                object_info = ""

                if action == "add":
                    obj_type = entry["result"].get("object_type", "object")
                    quantity = entry["result"].get("quantity", 1)
                    if quantity > 1:
                        object_info = f"added {quantity} {obj_type}s"
                    else:
                        object_info = f"added {obj_type}"
                elif action == "remove":
                    obj_id = entry["result"].get("object_id", "object")
                    object_info = f"removed {obj_id}"
                elif action == "move":
                    obj_id = entry["result"].get("object_id", "object")
                    target = entry["result"].get("target_object", "somewhere")
                    object_info = f"moved {obj_id} to {target}"

                context_lines.append(f"{i}. \"{entry['command']}\" -> {object_info}")

        return "\n".join(context_lines)

    def parse_spatial_command(self, command: str, scene_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a spatial command using LLM."""

        # Build context about current scene
        objects_list = []
        for obj_id, node in scene_context.get("objects", {}).items():
            objects_list.append(f"- {obj_id} ({node.cls}) at position {node.pos}")

        objects_context = "\\n".join(objects_list) if objects_list else "No objects in scene"

        # Build conversation context
        conversation_context = self.get_conversation_context()

        # System prompt for spatial command parsing
        system_prompt = f"""You are a spatial reasoning AI that parses natural language commands for a 3D scene manipulation system.

Current scene contains these objects:
{objects_context}

{conversation_context}

IMPORTANT: Use conversation history to resolve object references!
- "the two cups" refers to cups from previous commands
- "move the cups" means MOVE existing cups, not ADD new ones
- When user says "the X", look for existing X objects in the scene
- For MOVE commands, always use existing object_id from the scene

Your task is to parse user commands into structured JSON format. Return ONLY valid JSON with these fields:

{{
  "action": "add|move|remove|modify",
  "object_type": "standardized_object_name",
  "object_id": "unique_id_for_object",
  "target_object": "existing_object_id_or_null",
  "spatial_relation": "on_top_of|near|custom",
  "position": [x, y, z] or null,
  "properties": {{"additional": "properties", "spatial_description": "natural_language_description"}},
  "quantity": 1,
  "confidence": 0.0-1.0
}}

Object types should be standardized (e.g., "cup" -> "coffee_cup", "mug" -> "coffee_cup").

For ADD actions:
- Generate unique object_id like "coffee_cup_1", "book_2", etc.
- If spatial relation specified, set target_object to existing object
- Position will be calculated based on spatial relation

For MOVE actions:
- ALWAYS use existing object_id from scene (e.g., "coffee_cup_1", "coffee_cup_2")
- For "move the two cups", find all cup objects in scene and move the first 2
- Use quantity field to indicate how many objects to move
- Set target_object and spatial_relation for new position
- NEVER create new objects for MOVE commands

For REMOVE actions:
- Use existing object_id from scene
- Other fields can be null

QUANTITY HANDLING:
- Extract quantity from words like "two", "three", "several", "a few", "many"
- Numbers: "2 cups", "5 books" -> quantity: 2, 5
- Words: "two cups", "several books", "a few plates" -> quantity: 2, 3, 3
- Default to quantity: 1 for single objects

SPATIAL RELATIONS:
- "on_top_of": Object should be placed on the surface of target
- "near": Object should be placed close to target
- "custom": Complex spatial relationship - provide calculated position AND spatial_description

For CUSTOM spatial relations:
- Calculate the exact position based on the spatial relationship
- Include spatial_description in properties explaining the relationship
- Use scene context to determine optimal placement

Examples:
- "put a coffee cup on the table" -> {{"action": "add", "object_type": "coffee_cup", "object_id": "coffee_cup_1", "target_object": "table_1", "spatial_relation": "on_top_of", "quantity": 1, "confidence": 0.95}}
- "add a chair between the table and stove" -> {{"action": "add", "object_type": "chair", "object_id": "chair_2", "spatial_relation": "custom", "position": [2.45, 1.35, 0.45], "properties": {{"spatial_description": "between table_1 and stove"}}, "quantity": 1, "confidence": 0.90}}
- "place a lamp in the corner" -> {{"action": "add", "object_type": "lamp", "object_id": "lamp_1", "spatial_relation": "custom", "position": [0.2, 0.2, 0.25], "properties": {{"spatial_description": "in corner of room"}}, "confidence": 0.85}}

IMPORTANT: For ground-level objects, calculate Z coordinate as: ground_level + object_height/2
- Chairs (height 0.9m): Z = 0.0 + 0.9/2 = 0.45
- Tables (height 0.75m): Z = 0.0 + 0.75/2 = 0.375
- Small objects like cups (height 0.1m): Z = 0.0 + 0.1/2 = 0.05

Return ONLY the JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this command: {command}"}
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=500
            )

            # Extract and parse JSON response
            response_text = response.choices[0].message.content.strip()

            # Handle potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            try:
                parsed_result = json.loads(response_text)
                return parsed_result
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response text: {response_text}")
                return None

        except Exception as e:
            print(f"LLM API error: {e}")
            return None

    def enhance_object_properties(self, object_type: str) -> Dict[str, Any]:
        """Get enhanced properties for an object type using LLM."""

        system_prompt = """You are a 3D object property expert. Given an object type, return realistic physical properties in JSON format.

Return ONLY valid JSON with these fields:
{
  "bbox": {"type": "OBB", "xyz": [width, height, depth_in_meters]},
  "affordances": ["list", "of", "affordances"],
  "material": "material_type",
  "weight_kg": estimated_weight,
  "color": "typical_color",
  "fragility": "low|medium|high",
  "confidence": 0.0-1.0
}

Examples:
- coffee_cup -> {"bbox": {"type": "OBB", "xyz": [0.08, 0.08, 0.10]}, "affordances": ["hold_liquid", "portable"], "material": "ceramic", "weight_kg": 0.3, "color": "white", "fragility": "medium", "confidence": 0.95}
- laptop -> {"bbox": {"type": "OBB", "xyz": [0.35, 0.25, 0.03]}, "affordances": ["computing", "portable"], "material": "plastic_metal", "weight_kg": 2.0, "color": "black", "fragility": "medium", "confidence": 0.98}

Return ONLY the JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Properties for: {object_type}"}
                ],
                temperature=0.2,
                max_tokens=300
            )

            response_text = response.choices[0].message.content.strip()

            # Handle potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback to default properties
                return self._get_default_properties(object_type)

        except Exception as e:
            print(f"LLM property enhancement error: {e}")
            return self._get_default_properties(object_type)

    def _get_default_properties(self, object_type: str) -> Dict[str, Any]:
        """Fallback default properties."""
        defaults = {
            "coffee_cup": {
                "bbox": {"type": "OBB", "xyz": [0.08, 0.08, 0.10]},
                "affordances": ["hold_liquid", "portable"],
                "material": "ceramic",
                "weight_kg": 0.3,
                "color": "white",
                "fragility": "medium",
                "confidence": 0.8
            },
            "book": {
                "bbox": {"type": "OBB", "xyz": [0.15, 0.23, 0.03]},
                "affordances": ["readable", "portable"],
                "material": "paper",
                "weight_kg": 0.5,
                "color": "varied",
                "fragility": "low",
                "confidence": 0.8
            }
        }

        return defaults.get(object_type, {
            "bbox": {"type": "OBB", "xyz": [0.1, 0.1, 0.1]},
            "affordances": ["portable"],
            "material": "unknown",
            "weight_kg": 1.0,
            "color": "gray",
            "fragility": "medium",
            "confidence": 0.5
        })
