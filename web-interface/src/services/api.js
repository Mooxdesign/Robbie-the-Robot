import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

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
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.ws.onopen = () => {
            console.log('[DEBUG] WebSocket connected');
            this.reconnectDelay = 1000;
        };
        this.ws.onmessage = (event) => {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                console.error('[DEBUG] Failed to parse WebSocket message:', event.data, e);
                return;
            }
            // Hybrid event dispatch: specialized listeners for high-frequency, state for holistic
            if (typeof data.audio_level !== 'undefined') {
                this._audioLevelListeners.forEach(cb => cb(data.audio_level));
            }
            if (typeof data.last_transcription !== 'undefined') {
                this._transcriptionListeners.forEach(cb => cb(data.last_transcription));
            }
            // Always dispatch to state listeners with the full state
            this._stateListeners.forEach(cb => cb(data));
        };
        this.ws.onerror = (error) => {
            console.error('[DEBUG] WebSocket error:', error, this.ws.readyState);
        };
        this.ws.onclose = (event) => {
            console.warn('[DEBUG] WebSocket closed:', event.code, event.reason, 'Reconnecting in', this.reconnectDelay, 'ms...');
            setTimeout(() => {
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
                this.initWebSocket();
            }, this.reconnectDelay);
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
