from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import Dict, Set
import logging
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Integrate RobotController state updates with WebSocket broadcast ---

main_event_loop = None

def robot_state_update_callback(update: dict):
    # Called by RobotController when state changes
    # Merge update into global robot_state and broadcast
    robot_state.update({k: v for k, v in update.items() if k in robot_state})
    # Broadcast full robot_state to all clients
    try:
        global main_event_loop
        if main_event_loop and main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(robot_state)), main_event_loop)
        else:
            logger.error("Main event loop is not running or not set.")
    except Exception as e:
        logger.error(f"Error broadcasting robot state: {e}")


@app.on_event("startup")
async def setup_robot_callback():
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
    from controller.robot import robot_instance
    if robot_instance and getattr(robot_instance, 'state_update_callback', None) is None:
        robot_instance.state_update_callback = robot_state_update_callback


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
        self._last_no_websocket_log = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        if not self.active_connections:
            now = time.time()
            if now - self._last_no_ws_log > 5:  # Log at most once every 5 seconds
                logging.debug("No WebSocket clients connected; broadcast skipped.")
                self._last_no_ws_log = now
            return
        to_remove = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.warning(f"WebSocket send failed, removing client: {e}")
                to_remove.add(connection)
        for connection in to_remove:
            self.active_connections.discard(connection)
        if to_remove:
            logging.info(f"Removed {len(to_remove)} disconnected WebSocket clients from active_connections.")

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
    "input_audio_level_db": 0.0,  # Real-time audio input level (dB or normalized)
    "output_audio_level_db": 0.0,  # Real-time audio output level (dB or normalized)
    "last_transcription": "",  # Latest Whisper AI transcription
    "last_response": "",  # Latest AI response
    "led_matrix": [],  # 8x4 RGB LED matrix state (list of lists)
    "chat_history": []  # Full chat history: list of {sender, text}
}

# --- LED Matrix State Integration ---
import numpy as np

def update_led_matrix_state(leds_module):
    """
    Update robot_state['led_matrix'] with the current LED buffer as a nested list.
    Should be called after each LED buffer update.
    """
    with leds_module._lock:
        # Convert the numpy buffer (4,8,3) to a nested list for JSON serialization
        robot_state['led_matrix'] = leds_module.buffer.astype(int).tolist()
        logger.debug(f"[DEBUG] update_led_matrix_state called. led_matrix: {robot_state['led_matrix']}")

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
                    if "input_audio_level_db" in command:
                        robot_state["input_audio_level_db"] = command["input_audio_level_db"]
                    if "output_audio_level_db" in command:
                        robot_state["output_audio_level_db"] = command["output_audio_level_db"]
                elif cmd_type == "update_transcription":
                    # Update transcription from robot controller/module
                    robot_state["last_transcription"] = command.get("last_transcription", "")
                elif cmd_type == "ping":
                    # Ignore keepalive pings
                    continue
                elif cmd_type == "chat":
                    # Handle typed chat from web interface
                    chat_text = command.get("text", "")
                    # Import robot controller instance
                    from controller.robot import robot_instance
                    response = None
                    if hasattr(robot_instance, "speech"):
                        # Simulate transcription callback
                        response = robot_instance.speech.on_transcription(chat_text)
                    # Always set last_transcription to the user prompt
                    robot_state["last_transcription"] = chat_text
                    # Always set last_response to the AI response (or empty string if none)
                    robot_state["last_response"] = response if response else ""

                    # Always update chat_history from conversation module
                    if hasattr(robot_instance, "conversation"):
                        robot_state["chat_history"] = robot_instance.conversation.get_chat_history()
                        # Broadcast chat_history as a dedicated message
                        import asyncio
                        asyncio.create_task(manager.broadcast(json.dumps({
                            "type": "chat_history",
                            "chat_history": robot_state["chat_history"]
                        })))

                elif cmd_type == "test_led":
                    from controller.robot import robot_instance
                    if robot_instance and hasattr(robot_instance, "leds"):
                        leds = robot_instance.leds
                        # Fill the entire buffer with magenta
                        leds.buffer[:, :] = [255, 0, 255]
                        logger.info("[DEBUG] test_led: buffer shape:", leds.buffer.shape)
                        leds.show()
                elif cmd_type == "wake":
                    from controller.robot import robot_instance
                    if robot_instance:
                        robot_instance.wake_up()
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
                break
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_movement(command: Dict):
    """Handle robot movement commands"""
    direction = command.get("direction")
    speed = command.get("speed", 50)
    # TODO: Implement actual robot movement control
    logger.info(f"Moving robot: {direction} at speed {speed}")

async def handle_configuration(command: Dict):
    """Handle robot configuration updates"""
    config = command.get("config", {})
    # TODO: Implement actual configuration updates
    logger.info(f"Updating configuration: {config}")

# Mount the static files (for the frontend)
import os

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web-interface", "dist"))
logger.info(f"Mounting static files from: {frontend_dist}")
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
