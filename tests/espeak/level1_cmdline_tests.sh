#!/bin/bash
# Level 1: Direct Command-Line Testing
# Purpose: Verify espeak is installed and working at the OS level

echo "=========================================="
echo "LEVEL 1: ESPEAK COMMAND-LINE TESTS"
echo "=========================================="
echo ""

# Test 1.1: Basic espeak installation
echo "Test 1.1: Checking espeak installation..."
if command -v espeak &> /dev/null; then
    echo "✓ espeak found at: $(which espeak)"
    espeak --version
else
    echo "✗ espeak not found. Install with: sudo apt-get install espeak"
    exit 1
fi
echo ""

# Test 1.2: Simple speech output
echo "Test 1.2: Testing basic speech output..."
echo "You should hear: 'Hello, I am Robbie the Robot'"
espeak "Hello, I am Robbie the Robot"
sleep 1
echo "✓ Basic speech test completed"
echo ""

# Test 1.3: Test different voices
echo "Test 1.3: Listing available voices..."
espeak --voices | head -20
echo ""
echo "Testing American English voice..."
espeak -v en-us "Testing American English voice"
sleep 1
echo "Testing British English voice..."
espeak -v en-gb "Testing British English voice"
sleep 1
echo "✓ Voice tests completed"
echo ""

# Test 1.4: Test speech rate and pitch
echo "Test 1.4: Testing speech rate and pitch..."
echo "Testing slower speech rate (140 wpm)..."
espeak -s 140 "Testing slower speech rate"
sleep 1
echo "Testing faster speech rate (200 wpm)..."
espeak -s 200 "Testing faster speech rate"
sleep 1
echo "Testing lower pitch..."
espeak -p 30 "Testing lower pitch"
sleep 1
echo "Testing higher pitch..."
espeak -p 70 "Testing higher pitch"
sleep 1
echo "✓ Rate and pitch tests completed"
echo ""

echo "=========================================="
echo "LEVEL 1 TESTS COMPLETED SUCCESSFULLY"
echo "=========================================="
