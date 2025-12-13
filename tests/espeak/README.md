# Espeak Testing Plan for Raspberry Pi

## Overview
The robot uses `pyttsx3` for TTS, which on Linux/Raspberry Pi uses `espeak` as the backend. This plan tests espeak integration from basic command-line functionality through to full conversation module integration.

## Running the Tests

### Level 0: Audio Diagnostics (START HERE!)
If you're not hearing audio, run this first:
```bash
cd tests/espeak
bash level0_audio_diagnostics.sh
```

Or for a quick Python test:
```bash
python3 quick_audio_test.py
```

If you have USB audio devices, configure them:
```bash
bash configure_usb_audio.sh
```

### Level 1: Command-Line Tests
```bash
cd tests/espeak
bash level1_cmdline_tests.sh
```

### Level 2-6: Python Tests
```bash
cd tests/espeak
python3 level2_pyttsx3_basic.py
python3 level3_voice_module.py
python3 level4_speech_controller.py
python3 level5_conversation_flow.py
python3 level6_robot_controller.py
```

## Success Criteria

- ✅ **Level 0:** Audio hardware is working and configured
- ✅ **Level 1:** espeak produces audio from command line
- ✅ **Level 2:** pyttsx3 can initialize and produce speech
- ✅ **Level 3:** VoiceModule thread management works correctly
- ✅ **Level 4:** SpeechController integrates with VoiceModule
- ✅ **Level 5:** Conversation responses are spoken correctly
- ✅ **Level 6:** Full robot system operates with speech

## Troubleshooting

See `troubleshooting.md` for common issues and solutions.
