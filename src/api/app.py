from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
    },
    "audio_level": 0.0,  # Real-time audio input level (dB or normalized)
    "last_transcription": ""  # Latest Whisper AI transcription
}

@app.get("/api/status")
async def get_status():
    return robot_state

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send the current robot_state immediately to the new client
    await websocket.send_text(json.dumps(robot_state))
    try:
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    command = json.loads(data)
                except json.JSONDecodeError as e:
                    logging.warning(f"Malformed JSON received in /ws: {data} ({e})")
                    continue

                # Handle different command types
                cmd_type = command.get("type")
                if cmd_type == "move":
                    await handle_movement(command)
                elif cmd_type == "config":
                    await handle_configuration(command)
                elif cmd_type == "update_audio_level":
                    # Update audio level from robot controller/module
                    robot_state["audio_level"] = command.get("audio_level", 0.0)
                elif cmd_type == "update_transcription":
                    # Update transcription from robot controller/module
                    robot_state["last_transcription"] = command.get("last_transcription", "")
                elif cmd_type == "ping":
                    # Ignore keepalive pings
                    continue
                else:
                    logging.info(f"Unknown WebSocket command type: {cmd_type}")
                    continue

                # Broadcast updated state
                await manager.broadcast(json.dumps(robot_state))
            except WebSocketDisconnect:
                logging.info("WebSocket client disconnected.")
                break
            except Exception as e:
                logging.error(f"WebSocket loop error: {e}")
                continue
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

# Mount the static files (for the frontend)
import os

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web-interface", "dist"))
print(f"Mounting static files from: {frontend_dist}")
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
