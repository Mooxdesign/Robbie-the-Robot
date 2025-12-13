# Espeak Testing Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "espeak: command not found"

**Symptom:** Command-line tests fail with "command not found"

**Solution:**
```bash
sudo apt-get update
sudo apt-get install espeak
```

**Verification:**
```bash
which espeak
espeak --version
```

---

### Issue 2: No audio output

**Symptom:** Commands run but no sound is produced

**Solutions:**

1. **Check audio devices:**
```bash
aplay -l
```

2. **Test audio system:**
```bash
speaker-test -t wav -c 2
```

3. **Adjust volume:**
```bash
alsamixer
# Use arrow keys to adjust, ESC to exit
```

4. **Check audio output device:**
```bash
# For Raspberry Pi, ensure audio is routed to correct output
sudo raspi-config
# Navigate to: System Options > Audio > Select output device
```

5. **Test with a simple sound:**
```bash
aplay /usr/share/sounds/alsa/Front_Center.wav
```

---

### Issue 3: pyttsx3 can't find espeak

**Symptom:** Python tests fail with "No module named 'pyttsx3'" or engine initialization errors

**Solutions:**

1. **Verify espeak is in PATH:**
```bash
which espeak
echo $PATH
```

2. **Reinstall pyttsx3:**
```bash
pip3 uninstall pyttsx3
pip3 install pyttsx3
```

3. **Check Python version:**
```bash
python3 --version
# Should be Python 3.7 or higher
```

---

### Issue 4: Permission errors

**Symptom:** "Permission denied" errors when accessing audio

**Solutions:**

1. **Add user to audio group:**
```bash
sudo usermod -a -G audio $USER
```

2. **Logout and login again** (or reboot)

3. **Verify group membership:**
```bash
groups
# Should include 'audio'
```

---

### Issue 5: "ALSA lib ... underrun occurred"

**Symptom:** Audio plays but with warnings about buffer underruns

**Solutions:**

1. **This is usually harmless** - audio should still work

2. **If audio is choppy, try increasing buffer size** in config.yaml:
```yaml
audio:
  chunk_size: 2048  # Increase from 1024
```

---

### Issue 6: OpenAI API errors in Level 5/6 tests

**Symptom:** "No API key provided" or authentication errors

**Solutions:**

1. **Set OpenAI API key:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

2. **Add to .bashrc for persistence:**
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

3. **Or create .env file:**
```bash
cd ~/Robbie-the-Robot
echo 'OPENAI_API_KEY=your-api-key-here' > .env
```

---

### Issue 7: Motor/Hardware errors in Level 6

**Symptom:** Errors about I2C, GPIO, or hardware not found

**Solutions:**

1. **This is expected if testing on non-Pi hardware**

2. **On Raspberry Pi, enable I2C:**
```bash
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable
```

3. **Install required libraries:**
```bash
pip3 install adafruit-circuitpython-motorkit
pip3 install adafruit-circuitpython-servokit
```

---

### Issue 8: VoiceModule thread not starting

**Symptom:** "Speech thread not running" warnings

**Solutions:**

1. **Check for exceptions in initialization:**
```python
# Add more debug output
voice = VoiceModule(debug=True)
time.sleep(3)  # Give more time to initialize
```

2. **Check system resources:**
```bash
top
# Ensure CPU/memory are not maxed out
```

---

### Issue 9: Robotic/poor quality voice

**Symptom:** Voice sounds very robotic or unclear

**Solutions:**

1. **This is normal for espeak** - it's a formant synthesizer

2. **Try different voices:**
```bash
espeak --voices
espeak -v en-us+f3 "Testing female voice"
espeak -v en-gb+m3 "Testing male voice"
```

3. **Adjust speech rate:**
```bash
espeak -s 140 "Slower is often clearer"
```

4. **For better quality, consider installing festival:**
```bash
sudo apt-get install festival
# Then modify VoiceModule to use festival backend
```

---

### Issue 10: Tests hang or freeze

**Symptom:** Test scripts stop responding

**Solutions:**

1. **Kill the process:**
```bash
# Press Ctrl+C
# If that doesn't work:
ps aux | grep python
kill -9 <PID>
```

2. **Check for deadlocks in threading:**
```bash
# Add timeout to blocking calls
voice.say("test", blocking=True)
# Add timeout parameter if available
```

3. **Restart from a clean state:**
```bash
sudo reboot
```

---

## Debugging Tips

### Enable verbose logging

Add to test scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check system logs

```bash
# Check system messages
dmesg | tail -50

# Check audio-specific logs
journalctl -u alsa-state -n 50
```

### Test in isolation

If a test fails, run components individually:
```python
# Test just pyttsx3
import pyttsx3
engine = pyttsx3.init()
engine.say("test")
engine.runAndWait()
```

### Monitor resource usage

```bash
# CPU and memory
htop

# Audio processes
ps aux | grep -E 'pulse|alsa|espeak'
```

---

## Getting Help

If issues persist:

1. Check the project's GitHub issues
2. Review pyttsx3 documentation: https://pyttsx3.readthedocs.io/
3. Check Raspberry Pi forums for audio issues
4. Verify all dependencies are installed: `pip3 list`
