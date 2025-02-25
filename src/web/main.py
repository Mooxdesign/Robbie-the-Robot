from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import Dict, Set
import logging

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections store
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"Error sending message: {e}")

manager = ConnectionManager()

# Robot state
robot_state = {
    "connected": False,
    "battery": 0,
    "temperature": 0,
    "position": {"x": 0, "y": 0, "z": 0},
    "rotation": 0,
    "sensors": {
        "front": 0,
        "rear": 0,
        "left": 0,
        "right": 0
    }
}

@app.get("/api/status")
async def get_status():
    return robot_state

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            # Handle different command types
            if command["type"] == "move":
                # TODO: Implement robot movement control
                await handle_movement(command)
            elif command["type"] == "config":
                # TODO: Implement configuration updates
                await handle_configuration(command)
            
            # Broadcast updated state
            await manager.broadcast(json.dumps(robot_state))
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_movement(command: Dict):
    """Handle robot movement commands"""
    direction = command.get("direction")
    speed = command.get("speed", 50)
    # TODO: Implement actual robot movement control
    print(f"Moving robot: {direction} at speed {speed}")

async def handle_configuration(command: Dict):
    """Handle robot configuration updates"""
    config = command.get("config", {})
    # TODO: Implement actual configuration updates
    print(f"Updating configuration: {config}")

# Mount the static files (will be used after building the Vue.js app)
app.mount("/", StaticFiles(directory="web-interface/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
