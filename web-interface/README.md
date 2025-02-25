# Robbie the Robot Web Interface

This is the web interface for Robbie the Robot, built with Vue 3. It provides a modern, responsive interface for configuring, controlling, virtualizing, and debugging the robot.

## Features

- Robot Configuration Management
- Real-time Robot Control
- 3D Visualization
- Debugging Interface
- System Status Monitoring

## Setup Instructions

1. Install Node.js and npm (Node Package Manager)
2. Install project dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## Project Structure

```
web-interface/
├── src/
│   ├── assets/          # Static assets
│   ├── components/      # Vue components
│   ├── views/           # Page components
│   ├── stores/          # Pinia stores
│   ├── services/        # API services
│   └── utils/           # Utility functions
├── public/              # Public static files
└── index.html          # Entry HTML file
```

## Development

This project uses:
- Vue 3 with Composition API
- Pinia for state management
- Vue Router for routing
- Three.js for 3D visualization
- Tailwind CSS for styling
