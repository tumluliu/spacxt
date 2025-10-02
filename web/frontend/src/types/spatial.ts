// TypeScript types for SpacXT Spatial Context

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}

export interface BoundingBox {
  type: string;
  xyz: [number, number, number];
}

export interface SpatialObject {
  id: string;
  name?: string;
  type: string;
  position: [number, number, number];
  orientation: [number, number, number, number];
  bbox: BoundingBox;
  affordances: string[];
  level_of_mobility: string;
  confidence: number;
  state: Record<string, any>;
  meta: {
    color?: string;
    material?: string;
    [key: string]: any;
  };
}

export interface SpatialRelationship {
  type: string;
  from: string;
  to: string;
  confidence: number;
  properties?: Record<string, any>;
}

export interface SupportRelationship {
  support_relationships: Record<string, string>;
  dependents: Record<string, string[]>;
  recursive_dependents?: Record<string, string[]>;
  total_supported_objects?: number;
  total_supporting_objects?: number;
}

export interface SceneState {
  objects: Record<string, SpatialObject>;
  relationships: SpatialRelationship[];
  support_relationships: SupportRelationship;
  timestamp: string;
  activity_logs?: Array<{
    timestamp: string;
    type: string;
    message: string;
  }>;
}

export interface CommandResult {
  success: boolean;
  command?: string;
  parsed?: any;
  result?: string;
  message?: string;
  scene?: SceneState;
}

export interface QuestionResult {
  success: boolean;
  question: string;
  answer: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'scene_update' | 'error' | 'pong' | 'command_result';
  data?: any;
  message?: string;
}

export interface ObjectCreateRequest {
  object_type: string;
  position?: [number, number, number];
  target_object?: string;
  spatial_relation?: string;
  quantity?: number;
}

export interface NLCommandRequest {
  command: string;
  session_id?: string;
}

export interface SpatialQuestionRequest {
  question: string;
  session_id?: string;
}
