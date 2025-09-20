// API service for communicating with SpacXT backend

import axios from 'axios';
import {
  SceneState,
  CommandResult,
  QuestionResult,
  ObjectCreateRequest,
  NLCommandRequest,
  SpatialQuestionRequest
} from '../types/spatial';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request/response interceptors for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export class SpatialAPI {
  static async getScene(sessionId: string = 'default'): Promise<SceneState> {
    const response = await api.get(`/api/scene/${sessionId}`);
    return response.data;
  }

  static async createObject(
    objectData: ObjectCreateRequest,
    sessionId: string = 'default'
  ): Promise<CommandResult> {
    const response = await api.post(`/api/objects/${sessionId}`, objectData);
    return response.data;
  }

  static async executeCommand(
    command: NLCommandRequest,
    sessionId: string = 'default'
  ): Promise<CommandResult> {
    const response = await api.post(`/api/commands/${sessionId}`, command);
    return response.data;
  }

  static async askQuestion(
    question: SpatialQuestionRequest,
    sessionId: string = 'default'
  ): Promise<QuestionResult> {
    const response = await api.post(`/api/questions/${sessionId}`, question);
    return response.data;
  }

  static async deleteObject(
    objectId: string,
    sessionId: string = 'default'
  ): Promise<CommandResult> {
    const response = await api.delete(`/api/objects/${sessionId}/${objectId}`);
    return response.data;
  }

  static async runSimulationStep(sessionId: string = 'default'): Promise<CommandResult> {
    const response = await api.post(`/api/simulate/${sessionId}`);
    return response.data;
  }

  static createWebSocket(sessionId: string = 'default'): WebSocket {
    return new WebSocket(`${WS_BASE_URL}/ws/${sessionId}`);
  }
}

export default SpatialAPI;
