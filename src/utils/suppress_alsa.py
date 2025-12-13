"""
Suppress ALSA warnings on Linux
Import this module early to hide ALSA lib warnings
"""
import os
import sys
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

def suppress_alsa_warnings():
    """Suppress ALSA warnings by redirecting stderr"""
    if sys.platform.startswith('linux'):
        try:
            # Define error handler
            ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
            
            def py_error_handler(filename, line, function, err, fmt):
                pass
            
            c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
            
            try:
                asound = cdll.LoadLibrary('libasound.so.2')
                asound.snd_lib_error_set_handler(c_error_handler)
            except:
                pass
        except:
            pass

# Auto-suppress when imported
suppress_alsa_warnings()
