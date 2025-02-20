# RPi 5 Robot Controller

This project implements a robot controller for Raspberry Pi 5 with the following components:
- Servo HAT for servo motor control
- DC Motor HAT for DC motor control
- Xbox 360 wireless controller support
- Google Coral Edge TPU for AI acceleration
- Unicorn pHAT for LED display

## Hardware Requirements

- Raspberry Pi 5
- Adafruit 16-Channel PWM/Servo HAT
- Adafruit DC & Stepper Motor HAT
- Xbox 360 Wireless Receiver for Windows
- Google Coral USB Accelerator
- Pimoroni Unicorn pHAT
- Power supply (5V for RPi, separate power for motors)

## Software Setup

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev i2c-tools
sudo raspi-config  # Enable I2C interface
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up the Coral USB Accelerator:
```bash
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install libedgetpu1-std
```

4. Configure I2C for the HATs:
```bash
# Add the following lines to /etc/modules
i2c-dev
i2c-bcm2708
```

## Usage

1. Connect all hardware components:
   - Mount the Servo HAT and DC Motor HAT on the RPi
   - Connect the Xbox 360 receiver via USB
   - Connect the Coral USB Accelerator
   - Mount the Unicorn pHAT

2. Run the robot controller:
```bash
python3 src/robot_controller.py
```

## Controls

- Left analog stick: Control robot movement
  - Up/Down: Forward/Backward
  - Left/Right: Turn left/right
- Right analog stick: Control servo position
  - X-axis: Pan
  - Y-axis: Tilt

## Voice Commands

Supported commands:
- "Hey robot stop" - Emergency stop
- "Hey robot calibrate" - Start calibration
- "Hey robot manual mode" - Switch control mode

To train voice model:
```bash
python -m src.robot_controller --train-voice
```

## Documentation

Our comprehensive documentation is built with Docusaurus:
```bash
cd docs/
npm install
npm start
```

Access:
- Local: http://localhost:3000
- Live: https://your-username.github.io/rpi5-robot

## Notes for WSL Usage

When running in WSL, some hardware-specific features will be simulated. To test the full functionality, deploy the code to a physical Raspberry Pi 5.

## License

MIT License
