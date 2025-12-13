#!/bin/bash
# Level 0: Audio System Diagnostics
# Purpose: Verify audio hardware and configuration before espeak tests

echo "=========================================="
echo "LEVEL 0: AUDIO SYSTEM DIAGNOSTICS"
echo "=========================================="
echo ""

# Check audio devices
echo "Test 0.1: Listing audio playback devices..."
aplay -l
echo ""

# Check audio cards
echo "Test 0.2: Listing audio cards..."
cat /proc/asound/cards
echo ""

# Check default audio device
echo "Test 0.3: Checking default audio device..."
aplay -L | grep -A2 "^default"
echo ""

# Test with a simple WAV file (if available)
echo "Test 0.4: Testing audio output with system sound..."
if [ -f /usr/share/sounds/alsa/Front_Center.wav ]; then
    echo "Playing test sound... (you should hear audio)"
    aplay /usr/share/sounds/alsa/Front_Center.wav
    echo "Did you hear the test sound? (y/n)"
    read -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "✓ Audio hardware is working"
    else
        echo "✗ Audio hardware issue - check connections and volume"
    fi
else
    echo "⚠ No test sound file found, skipping hardware test"
fi
echo ""

# Check ALSA configuration
echo "Test 0.5: Checking ALSA mixer settings..."
echo "Current volume levels:"
amixer scontrols
echo ""
echo "Master volume:"
amixer get Master 2>/dev/null || amixer get PCM 2>/dev/null || echo "No Master/PCM control found"
echo ""

# Check if PulseAudio is running
echo "Test 0.6: Checking for PulseAudio..."
if pgrep -x pulseaudio > /dev/null; then
    echo "✓ PulseAudio is running"
    pactl list sinks short 2>/dev/null || echo "⚠ Could not list PulseAudio sinks"
else
    echo "⚠ PulseAudio is not running (using ALSA directly)"
fi
echo ""

# Check USB audio devices specifically
echo "Test 0.7: Checking USB audio devices..."
lsusb | grep -i audio
echo ""

# Test espeak with explicit device
echo "Test 0.8: Testing espeak with default device..."
if command -v espeak &> /dev/null; then
    echo "You should hear: 'Testing default audio device'"
    espeak "Testing default audio device"
    echo "Did you hear espeak? (y/n)"
    read -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "✓ Espeak audio is working"
    else
        echo "✗ Espeak audio issue"
        echo ""
        echo "Trying to set audio output device..."
        echo "Available ALSA devices:"
        aplay -L | grep -E "^(hw:|plughw:|default)"
    fi
else
    echo "✗ espeak not installed"
fi
echo ""

# Check for common audio issues
echo "Test 0.9: Checking for common issues..."

# Check if user is in audio group
if groups | grep -q audio; then
    echo "✓ User is in 'audio' group"
else
    echo "✗ User is NOT in 'audio' group"
    echo "  Fix with: sudo usermod -a -G audio $USER"
    echo "  Then logout and login again"
fi

# Check if audio device is muted
MUTED=$(amixer get Master 2>/dev/null | grep -o "\[off\]" | head -1)
if [ -z "$MUTED" ]; then
    echo "✓ Audio is not muted"
else
    echo "✗ Audio is MUTED"
    echo "  Fix with: amixer set Master unmute"
fi

# Check volume level
VOLUME=$(amixer get Master 2>/dev/null | grep -o "[0-9]*%" | head -1 | tr -d '%')
if [ -n "$VOLUME" ]; then
    if [ "$VOLUME" -gt 30 ]; then
        echo "✓ Volume is at ${VOLUME}%"
    else
        echo "⚠ Volume is low (${VOLUME}%)"
        echo "  Increase with: amixer set Master 80%"
    fi
else
    echo "⚠ Could not determine volume level"
fi

echo ""
echo "=========================================="
echo "DIAGNOSTICS COMPLETE"
echo "=========================================="
echo ""
echo "RECOMMENDATIONS:"
echo "1. Ensure USB speaker is connected and powered"
echo "2. Check volume with: alsamixer"
echo "3. Test audio with: speaker-test -t wav -c 2"
echo "4. If using specific USB device, you may need to set default in ~/.asoundrc"
echo ""
