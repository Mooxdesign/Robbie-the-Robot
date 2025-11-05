import axios from 'axios';

const API_HOST = process.env.VUE_APP_API_HOST || 'http://localhost:8000';
const API_URL = `${API_HOST}/api`;

export const api = {
    // WebSocket connection
    ws: null,
    reconnectDelay: 1000,
    _audioLevelListeners: [],
    _transcriptionListeners: [],
    _stateListeners: [],

    // Listener registration (Hybrid Approach)
    registerAudioLevelListener(cb) {
        this._audioLevelListeners.push(cb);
    },
    unregisterAudioLevelListener(cb) {
        this._audioLevelListeners = this._audioLevelListeners.filter(fn => fn !== cb);
    },
    registerTranscriptionListener(cb) {
        this._transcriptionListeners.push(cb);
    },
    unregisterTranscriptionListener(cb) {
        this._transcriptionListeners = this._transcriptionListeners.filter(fn => fn !== cb);
    },
    registerStateListener(cb) {
        this._stateListeners.push(cb);
    },
    unregisterStateListener(cb) {
        this._stateListeners = this._stateListeners.filter(fn => fn !== cb);
    },

    // WebSocket connection
    initWebSocket() {
        if (this.ws) {
            this.ws.close();
        }
        const wsHost = API_HOST.replace(/^http:\/\//, '');
        this.ws = new WebSocket(`ws://${wsHost}/ws`);

        this.ws.onopen = () => {
            console.log("[api.js] WebSocket connected");
            if (this.reconnectDelay) {
                clearTimeout(this.reconnectDelay);
                this.reconnectDelay = null;
            }
        };
        this.ws.onerror = (event) => {
            console.error("[api.js] WebSocket error:", event);
            // Optionally close to trigger onclose and reconnect
            this.ws.close();
        };

        this.ws.onclose = (event) => {
            console.warn('[DEBUG] WebSocket closed:', event.code, event.reason, 'Reconnecting in', this.reconnectDelay, 'ms...');
            this.isConnected = false;
            setTimeout(() => {
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
                this.initWebSocket();
            }, this.reconnectDelay);
        };

        this.ws.onmessage = (event) => {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                console.error('[api.js] Failed to parse WebSocket message:', event.data, e);
                return;
            }
            // Only handle audio level as a special case
            if (typeof data.audio_level !== 'undefined') {
                this._audioLevelListeners.forEach(cb => cb(data.audio_level));
                // Do NOT trigger full state update for audio level only
                return;
            }
            // Handle transcription listeners
            if (typeof data.last_transcription !== 'undefined') {
                this._transcriptionListeners.forEach(cb => cb(data.last_transcription));
            }
            // For all other state changes, trigger full state update
            this._stateListeners.forEach(cb => cb(data));
        };
        this.ws.onerror = (error) => {
            console.error('[api.js] WebSocket error:', error, this.ws.readyState);
        };
    },


    // WebSocket callbacks
    onMessage: null,
    onError: null,
    onClose: null,

    // (Deprecated) Real-time single listeners (use registerXListener instead)
    // onAudioLevel: null,
    // onTranscription: null,
    
    // Send a chat message to the robot (typed chat)
    sendChat(text) {
        this.sendCommand({
            type: 'chat',
            text
        });
    },

    // Listeners for robot state updates (already handled above; do not duplicate)
    // _stateListeners: [],
    // registerStateListener(cb) { ... },
    _notifyStateListeners(state) {
        this._stateListeners.forEach(cb => cb(state));
    },
    
    // Send command through WebSocket
    sendCommand(command) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(command));
        } else {
            console.error('WebSocket is not connected');
        }
    },
    
    // Robot control commands
    async moveRobot(direction, speed) {
        this.sendCommand({
            type: 'move',
            direction,
            speed
        });
    },
    
    async stopRobot() {
        this.sendCommand({
            type: 'move',
            direction: 'stop'
        });
    },
    
    // Configuration management
    async saveConfig(config) {
        this.sendCommand({
            type: 'config',
            config
        });
    },
    
    async setSpeechBackend(backend) {
        try {
            const response = await axios.post(`${API_URL}/speech/backend`, { backend });
            return response.data;
        } catch (error) {
            console.error('Error setting speech backend:', error);
            throw error;
        }
    },
    async getStatus() {
        try {
            const response = await axios.get(`${API_URL}/status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching status:', error);
            throw error;
        }
    },
    
    // Debug and testing
    async runTest(testName) {
        this.sendCommand({
            type: 'test',
            name: testName
        });
    },
    
    async calibrateSensor(sensorName) {
        this.sendCommand({
            type: 'calibrate',
            sensor: sensorName
        });
    }
}

// Initialize WebSocket connection when the service is imported
api.initWebSocket();
