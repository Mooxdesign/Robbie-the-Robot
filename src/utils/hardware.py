import os
import platform
import subprocess
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi"""
    logger.info("Hardware detected: Running on Raspberry Pi!")
    return platform.machine().startswith('arm') or platform.machine().startswith('aarch')

def check_i2c_device(address: int) -> bool:
    """
    Check if an I2C device is available at the specified address
    
    Args:
        address: I2C address in hex (e.g. 0x40 for PCA9685)
        
    Returns:
        bool: True if device is available
    """
    try:
        # Only attempt I2C detection on Raspberry Pi
        if not is_raspberry_pi():
            logger.info("No hardware detected: Running in simulation mode.")
            return False
            
        # Use i2cdetect to check for device
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                             capture_output=True, 
                             text=True)
        
        # Parse output to check if address is present
        hex_addr = hex(address)[2:] # Remove '0x' prefix
        return hex_addr in result.stdout
        
    except Exception as e:
        logger.error(f"Failed to check I2C device: {e}")
        return False

def check_camera() -> bool:
    """
    Check if Pi Camera is available
    
    Returns:
        bool: True if camera is available
    """
    try:
        # Only attempt camera detection on Raspberry Pi
        if not is_raspberry_pi():
            logger.info("No hardware detected: Running in simulation mode.")
            return False
            
        # Check if camera device exists
        return os.path.exists('/dev/video0')
        
    except Exception as e:
        logger.error(f"Failed to check camera: {e}")
        return False

def check_unicorn_hat() -> bool:
    """
    Check if Unicorn HAT Mini is available
    
    Returns:
        bool: True if Unicorn HAT is available
    """
    try:
        # Unicorn HAT uses the SPI interface
        if not is_raspberry_pi():
            logger.info("No hardware detected: Running in simulation mode.")
            return False
            
        # Check if SPI is enabled
        return os.path.exists('/dev/spidev0.0')
        
    except Exception as e:
        logger.error(f"Failed to check Unicorn HAT: {e}")
        return False

def check_motor_controller() -> Tuple[bool, bool]:
    """
    Check if motor controller (PCA9685) and servo controller are available
    
    Returns:
        Tuple[bool, bool]: (motor_available, servo_available)
    """
    # PCA9685 typically uses address 0x40
    return check_i2c_device(0x40), check_i2c_device(0x40)

# Hardware availability flags
CAMERA_AVAILABLE = check_camera()
MOTORS_AVAILABLE, SERVOS_AVAILABLE = check_motor_controller()
LED_AVAILABLE = check_unicorn_hat()
