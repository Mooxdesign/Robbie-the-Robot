#!/bin/bash
# Run all espeak tests in sequence
# This script runs all test levels from 1-6

echo "=========================================="
echo "ESPEAK INTEGRATION TEST SUITE"
echo "=========================================="
echo ""
echo "This will run all test levels:"
echo "  Level 1: Command-line espeak tests"
echo "  Level 2: pyttsx3 basic tests"
echo "  Level 3: VoiceModule integration"
echo "  Level 4: SpeechController integration"
echo "  Level 5: Conversation flow (requires API key)"
echo "  Level 6: Full robot controller"
echo ""
read -p "Press Enter to start tests (Ctrl+C to cancel)..."
echo ""

# Track test results
FAILED_TESTS=""

# Level 1: Command-line tests
echo ""
echo "=========================================="
echo "RUNNING LEVEL 1 TESTS"
echo "=========================================="
bash level1_cmdline_tests.sh
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level1"
    echo "✗ Level 1 tests FAILED"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Level 1 tests PASSED"
fi

# Level 2: pyttsx3 basic
echo ""
echo "=========================================="
echo "RUNNING LEVEL 2 TESTS"
echo "=========================================="
python3 level2_pyttsx3_basic.py
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level2"
    echo "✗ Level 2 tests FAILED"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Level 2 tests PASSED"
fi

# Level 3: VoiceModule
echo ""
echo "=========================================="
echo "RUNNING LEVEL 3 TESTS"
echo "=========================================="
python3 level3_voice_module.py
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level3"
    echo "✗ Level 3 tests FAILED"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Level 3 tests PASSED"
fi

# Level 4: SpeechController
echo ""
echo "=========================================="
echo "RUNNING LEVEL 4 TESTS"
echo "=========================================="
python3 level4_speech_controller.py
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level4"
    echo "✗ Level 4 tests FAILED"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Level 4 tests PASSED"
fi

# Level 5: Conversation flow
echo ""
echo "=========================================="
echo "RUNNING LEVEL 5 TESTS"
echo "=========================================="
echo "Note: This requires OPENAI_API_KEY to be set"
python3 level5_conversation_flow.py
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level5"
    echo "✗ Level 5 tests FAILED"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Level 5 tests PASSED"
fi

# Level 6: Full robot controller
echo ""
echo "=========================================="
echo "RUNNING LEVEL 6 TESTS"
echo "=========================================="
echo "Note: This initializes ALL robot subsystems"
python3 level6_robot_controller.py
if [ $? -ne 0 ]; then
    FAILED_TESTS="$FAILED_TESTS Level6"
    echo "✗ Level 6 tests FAILED"
else
    echo "✓ Level 6 tests PASSED"
fi

# Summary
echo ""
echo "=========================================="
echo "TEST SUITE SUMMARY"
echo "=========================================="
if [ -z "$FAILED_TESTS" ]; then
    echo "✓ ALL TESTS PASSED!"
    echo ""
    echo "Espeak is working correctly at all levels:"
    echo "  ✓ Command-line interface"
    echo "  ✓ pyttsx3 integration"
    echo "  ✓ VoiceModule"
    echo "  ✓ SpeechController"
    echo "  ✓ Conversation flow"
    echo "  ✓ Full robot system"
else
    echo "✗ SOME TESTS FAILED:"
    echo "$FAILED_TESTS"
    echo ""
    echo "See troubleshooting.md for common issues"
fi
echo "=========================================="
