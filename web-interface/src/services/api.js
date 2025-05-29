import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = {
    // WebSocket connection
    ws: null,

    // WebSocket callbacks
    onMessage: null,
    onError: null,
    onClose: null,

    // Real-time listeners
    onAudioLevel: null,
    onTranscription: null,
    
    reconnectDelay: 1000, // Start at 1s

    // Initialize WebSocket connection
    initWebSocket() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.ws.onopen = () => {
            console.log('[DEBUG] WebSocket connected');
            this.reconnectDelay = 1000; // Reset delay on successful connect
        };
        this.ws.onmessage = (event) => {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                console.error('[DEBUG] Failed to parse WebSocket message:', event.data, e);
                return;
            }
            if (this.onMessage) {
                this.onMessage(data);
            }
            // Audio level update
            if (typeof data.audio_level !== 'undefined') {
                console.log('[DEBUG] Received audio_level:', data.audio_level);
                if (this.onAudioLevel) {
                    this.onAudioLevel(data.audio_level);
                }
            }
            // Transcription update
            if (typeof data.last_transcription !== 'undefined' && this.onTranscription) {
                this.onTranscription(data.last_transcription);
            }
        };
        this.ws.onerror = (error) => {
            console.error('[DEBUG] WebSocket error:', error, this.ws.readyState);
            if (this.onError) {
                this.onError(error);
            }
        };
        this.ws.onclose = (event) => {
            console.warn('[DEBUG] WebSocket closed:', event.code, event.reason, 'Reconnecting in', this.reconnectDelay, 'ms...');
            setTimeout(() => {
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30s
                this.initWebSocket();
            }, this.reconnectDelay);
        };
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
};

// Register listeners for audio level and transcription
api.registerAudioLevelListener = function(cb) {
    this.onAudioLevel = cb;
};
api.registerTranscriptionListener = function(cb) {
    this.onTranscription = cb;
};

// Initialize WebSocket connection when the service is imported
api.initWebSocket();
