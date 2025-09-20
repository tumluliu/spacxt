# SpacXT Web Application

A professional web application showcasing the power of spatial context intelligence with natural language interaction and real-time 3D visualization.

## Architecture

- **Backend**: FastAPI service providing RESTful API and WebSocket support
- **Frontend**: Modern React application with Three.js 3D visualization
- **Real-time**: WebSocket connection for live scene updates
- **Professional UI**: Material-UI components with dark theme

## Features

### 🧠 Spatial Context Intelligence
- **Natural Language Commands**: "add a cup on the table", "move the chair closer to the stove"
- **Spatial Q&A**: "What objects are on the table?", "What if I remove the table?"
- **Real-time Updates**: Live synchronization between multiple clients
- **Physics Simulation**: Realistic object placement with gravity and collision detection

### 🎨 Professional 3D Visualization
- **Interactive 3D Scene**: Click and drag to explore, zoom in/out
- **Object Selection**: Click objects to inspect properties
- **Relationship Visualization**: Visual lines showing spatial relationships
- **Professional Lighting**: Realistic shadows and environment

### 🔧 Advanced Capabilities
- **Support System**: Objects move together when their supporter moves
- **Agent Negotiation**: Autonomous agents discover spatial relationships
- **Session Management**: Multiple concurrent sessions
- **Error Handling**: Graceful error recovery and user feedback

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- npm or yarn

### 1. Start Backend
```bash
cd backend
./start.sh
```
The API will be available at http://localhost:8000
- API docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/default

### 2. Start Frontend
```bash
cd frontend
./start.sh
```
The web app will be available at http://localhost:3000

## Usage

### Natural Language Commands
Try these commands in the web interface:
- `add a coffee cup on the table`
- `add two books on the chair`
- `move the cup to the stove`
- `put a mobile phone on the book`
- `move the table closer to the stove`

### Spatial Questions
Ask questions about the scene:
- `What objects are on the table?`
- `What if I remove the table?`
- `Which objects can I easily reach?`
- `What objects are near the stove?`

### Interactive Features
- **3D Scene**: Rotate, zoom, and pan the camera
- **Object Selection**: Click objects to see details
- **Real-time Updates**: Changes appear instantly
- **Settings**: Toggle relationship lines and grid

## API Endpoints

### REST API
- `GET /api/scene/{session_id}` - Get current scene state
- `POST /api/commands/{session_id}` - Execute natural language command
- `POST /api/questions/{session_id}` - Ask spatial question
- `POST /api/objects/{session_id}` - Create object
- `DELETE /api/objects/{session_id}/{object_id}` - Delete object
- `POST /api/simulate/{session_id}` - Run simulation step

### WebSocket
- `ws://localhost:8000/ws/{session_id}` - Real-time scene updates

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create `.env` files for configuration:

**Backend (.env)**:
```
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
```

**Frontend (.env)**:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation and serialization
- **SpacXT Core**: Spatial context management system

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Three.js**: 3D graphics and visualization
- **Material-UI**: Professional component library
- **Vite**: Fast build tool and dev server

## Deployment

### Production Build
```bash
# Backend
cd backend
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
# Serve dist/ folder with nginx or similar
```

### Docker (Optional)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Demo Scenarios

The application includes several impressive demo scenarios:

1. **Kitchen Scene**: Table, chair, stove with interactive objects
2. **Object Stacking**: Books, cups, phones with realistic physics
3. **Spatial Reasoning**: "between", "near", "on top of" relationships
4. **Dynamic Updates**: Move supporting objects, dependents follow
5. **Natural Language**: Complex commands with quantity parsing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**SpacXT - Spatial Context Intelligence**
*Bringing natural language understanding to 3D spatial reasoning*
