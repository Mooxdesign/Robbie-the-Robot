import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = {
    // WebSocket connection
    ws: null,
    
    // WebSocket callbacks
    onMessage: null,
    onError: null,
    onClose: null,
    
    // Initialize WebSocket connection
    initWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.onMessage) {
                this.onMessage(data);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (this.onError) {
                this.onError(error);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
            if (this.onClose) {
                this.onClose();
            }
            // Try to reconnect after 5 seconds
            setTimeout(() => this.initWebSocket(), 5000);
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

// Initialize WebSocket connection when the service is imported
api.initWebSocket();
