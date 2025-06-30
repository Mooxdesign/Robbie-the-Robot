import logging
import os
import sys

def setup_logging(debug: bool = False, log_file: str = 'robot.log'):
    """
    Set up logging configuration. If debug is True, set level to DEBUG, else INFO.
    Truncates the log file at the start of each run.
    """
    # Truncate (clear) the log file at the start of each run
    with open(log_file, 'w'):
        pass
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode='a')
        ]
    )
    # Reduce verbosity from noisy libraries
    logging.getLogger('comtypes').setLevel(logging.WARNING)
    logging.getLogger('comtypes.client').setLevel(logging.WARNING)
    logging.getLogger('comtypes.server').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
