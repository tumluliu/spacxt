# UUID Structure for Complex Apartment Scene

## Overview

All entities in the complex apartment scene now use UUIDs for unique identification, including the scene itself, all rooms, and all objects. Each entity also has a human-readable `name` field.

## UUID Assignment Scheme

### Scene UUID
- **Scene**: `550e8400-e29b-41d4-a716-446655440000`
  - Name: "Complex Apartment 101"

### Room UUIDs (441xxx series)
- **Living Room**: `550e8400-e29b-41d4-a716-446655441001`
- **Kitchen**: `550e8400-e29b-41d4-a716-446655441002`
- **Master Bedroom**: `550e8400-e29b-41d4-a716-446655441003`
- **Second Bedroom**: `550e8400-e29b-41d4-a716-446655441004`
- **Bathroom**: `550e8400-e29b-41d4-a716-446655441005`
- **Hallway**: `550e8400-e29b-41d4-a716-446655441006`

### Object UUIDs (440xxx series)

#### Living Room Objects
- **Living Room Sofa**: `550e8400-e29b-41d4-a716-446655440001`
- **Coffee Table**: `550e8400-e29b-41d4-a716-446655440002`
- **TV Stand**: `550e8400-e29b-41d4-a716-446655440003`
- **Television**: `550e8400-e29b-41d4-a716-446655440004`

#### Kitchen Objects
- **Kitchen Counter**: `550e8400-e29b-41d4-a716-446655440005`
- **Refrigerator**: `550e8400-e29b-41d4-a716-446655440006`
- **Kitchen Stove**: `550e8400-e29b-41d4-a716-446655440007`
- **Kitchen Chair 1**: `550e8400-e29b-41d4-a716-446655440008`
- **Kitchen Chair 2**: `550e8400-e29b-41d4-a716-446655440009`

#### Master Bedroom Objects
- **Master Bed**: `550e8400-e29b-41d4-a716-446655440010`
- **Master Nightstand Left**: `550e8400-e29b-41d4-a716-446655440011`
- **Master Nightstand Right**: `550e8400-e29b-41d4-a716-446655440012`
- **Master Wardrobe**: `550e8400-e29b-41d4-a716-446655440013`

#### Second Bedroom Objects
- **Second Bedroom Bed**: `550e8400-e29b-41d4-a716-446655440014`
- **Second Bedroom Desk**: `550e8400-e29b-41d4-a716-446655440015`
- **Office Chair**: `550e8400-e29b-41d4-a716-446655440016`

#### Bathroom Objects
- **Bathroom Toilet**: `550e8400-e29b-41d4-a716-446655440017`
- **Bathroom Sink**: `550e8400-e29b-41d4-a716-446655440018`
- **Bathroom Shower**: `550e8400-e29b-41d4-a716-446655440019`

#### Structural Elements (Walls & Doors)
- **Living Room Wall North**: `550e8400-e29b-41d4-a716-446655440020`
- **Living Room Wall East**: `550e8400-e29b-41d4-a716-446655440021`
- **Kitchen Wall North**: `550e8400-e29b-41d4-a716-446655440022`
- **Kitchen Wall East**: `550e8400-e29b-41d4-a716-446655440023`
- **Bedroom Wall West**: `550e8400-e29b-41d4-a716-446655440024`
- **Apartment Wall South**: `550e8400-e29b-41d4-a716-446655440025`
- **Living Room Door**: `550e8400-e29b-41d4-a716-446655440026`
- **Master Bedroom Door**: `550e8400-e29b-41d4-a716-446655440027`
- **Second Bedroom Door**: `550e8400-e29b-41d4-a716-446655440028`
- **Bathroom Door**: `550e8400-e29b-41d4-a716-446655440029`

## Relationship Examples

All relationships now use UUIDs for both subject and object references:

### Room Containment (IN relationships)
```json
{
  "r": "in",
  "a": "550e8400-e29b-41d4-a716-446655440001",  // Living Room Sofa
  "b": "550e8400-e29b-41d4-a716-446655441001",  // Living Room
  "conf": 1.0
}
```

### Object Support (ON_TOP_OF relationships)
```json
{
  "r": "on_top_of",
  "a": "550e8400-e29b-41d4-a716-446655440004",  // Television
  "b": "550e8400-e29b-41d4-a716-446655440003",  // TV Stand
  "conf": 1.0
}
```

### Discovered Spatial Relationships (BESIDE, ABOVE, etc.)
```json
{
  "r": "beside",
  "a": "550e8400-e29b-41d4-a716-446655440002",  // Coffee Table
  "b": "550e8400-e29b-41d4-a716-446655440001",  // Living Room Sofa
  "conf": 0.85
}
```

## Benefits of UUID Structure

### 1. **Global Uniqueness**
- Every entity has a globally unique identifier
- No naming conflicts between rooms and objects
- Supports distributed systems and merging scenes

### 2. **Type Identification**
- Scene: `...440000` (single scene)
- Rooms: `...441xxx` (room entities)
- Objects: `...440xxx` (physical objects)

### 3. **Human Readability**
- UUIDs provide unique technical identification
- `name` fields provide human-readable labels
- Export functions translate UUIDs to names for display

### 4. **Relationship Integrity**
- All relationships use UUIDs for precise referencing
- No ambiguity about which entities are related
- Confidence values preserved for all relationships

## Export Verification

The `complex_apartment_negotiated.json` file demonstrates:
- ✅ Scene uses UUID: `550e8400-e29b-41d4-a716-446655440000`
- ✅ All 6 rooms use UUIDs: `...441001` through `...441006`
- ✅ All 29 objects use UUIDs: `...440001` through `...440029`
- ✅ All 54 relationships reference entities by UUID
- ✅ All confidence values preserved (0.61 to 1.00)
- ✅ Names preserved for human readability

This structure provides the foundation for robust spatial scene management with complete traceability and unique identification for all entities.
