import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.append(src_path)

# Import simulation first to set verbosity
from simulation import hardware
hardware.VERBOSE = False  # Disable simulation output by default during tests
