# Complex Apartment Scene Demo

## Overview

This demo creates a realistic 80 square meter apartment with multiple rooms, walls, doors, and furniture. It demonstrates SpacXT's spatial relationship negotiation capabilities and includes functionality to export the complete scene graph with all discovered relationships and confidence values.

## Scene Structure

### Apartment Layout (~80 sqm)
- **Living Room** (6×5m): Main social area with sofa, coffee table, TV
- **Kitchen** (4×3m): Cooking area with appliances and dining space
- **Master Bedroom** (5×4m): Main bedroom with bed, nightstands, wardrobe
- **Second Bedroom** (3×3m): Smaller bedroom with bed and desk
- **Bathroom** (2×3m): Full bathroom with toilet, sink, shower
- **Hallway** (4×2m): Connecting corridor

### Objects (29 total)

#### Furniture with UUIDs and Names
Each object has:
- **UUID**: Unique identifier (e.g., `550e8400-e29b-41d4-a716-446655440001`)
- **Name**: Human-readable name (e.g., "Living Room Sofa", "Kitchen Chair 1")
- **Realistic dimensions**: Based on typical furniture sizes
- **Appropriate affordances**: sit, support, storage, etc.
- **Level of mobility**: fixed, low, medium, high

#### Structural Elements
- **Walls**: Fixed structural elements defining room boundaries
- **Doors**: Passage elements with open/closed state
- All structural elements have `lom: "fixed"`

## Files

### `complex_apartment.json`
Bootstrap scene definition with:
- Room definitions with bounding boxes
- 29 objects with UUIDs, names, positions, and properties
- Initial "in" relationships (objects in rooms)
- One explicit "on_top_of" relationship (TV on TV stand)

### `complex_apartment_demo.py`
Complete demo script that:
1. Loads the apartment scene
2. Creates 29 autonomous agents
3. Runs spatial relationship negotiation (15 rounds)
4. Exports results with confidence values
5. Provides detailed relationship summary

### `complex_apartment_negotiated.json` (Generated)
Export of the scene after negotiation containing:
- All original objects with current state
- **54 total relationships** (20 initial + 34 discovered)
- **Confidence values** for all relationships
- Export metadata and timestamp
- Negotiation history (last 10 events)

## Discovered Relationships

The agents discovered 34 new spatial relationships:

### Relationship Types Found
- **BESIDE** (16): Objects at similar heights positioned next to each other
  - Coffee Table ↔ Living Room Sofa (conf: 0.85)
  - Kitchen Stove ↔ Kitchen Counter (conf: 0.85)
  - Master Bed ↔ Nightstands (conf: 0.80)

- **ABOVE/BELOW** (18): Vertical spatial relationships
  - Television → TV Stand (conf: 0.64)
  - Walls above furniture items

- **IN** (19): Containment relationships (from bootstrap)
  - All furniture properly assigned to rooms (conf: 1.00)

- **ON_TOP_OF** (1): Direct support relationships
  - Television → TV Stand (conf: 1.00)

## Key Features

### UUID Support
- All objects use proper UUIDs for unique identification
- Names provide human-readable labels (may not be unique)
- Export preserves both UUID and name information

### Confidence Values
- All relationships include confidence scores (0.0-1.0)
- Higher confidence indicates stronger spatial evidence
- Export includes confidence for analysis and filtering

### Export Functionality
The `SceneExporter` class provides:
- Complete scene serialization with relationships
- Confidence value preservation
- Metadata including object/relationship counts
- Negotiation history tracking
- Readable relationship summaries

## Running the Demo

```bash
cd examples
python complex_apartment_demo.py
```

The demo will:
1. Load the 29-object apartment scene
2. Run 15 rounds of agent negotiation
3. Display discovered relationships by type
4. Export complete results to `complex_apartment_negotiated.json`

## Scene Statistics

- **Area**: ~80 square meters (10m × 8m)
- **Rooms**: 6 (including hallway)
- **Objects**: 29 total
  - Furniture: 19 items
  - Structural: 10 items (walls, doors)
- **Relationships**: 54 total after negotiation
  - Bootstrap: 20 relationships
  - Discovered: 34 relationships
- **Agent Negotiations**: 477 events during 15 rounds

This demonstrates SpacXT's ability to handle complex, realistic spatial scenes with autonomous relationship discovery and comprehensive data export capabilities.
