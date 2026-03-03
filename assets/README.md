# Assets Directory

## Audio Files

### chime.wav
Activation sound played when wake word is detected.

**Requirements:**
- Format: WAV
- Sample Rate: Any (typically 44.1kHz or 48kHz)
- Duration: 0.5-1.0 seconds recommended

**To generate a simple chime:**
```bash
# Using ffmpeg to generate a 440Hz tone (1 second)
ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -ar 44100 chime.wav
```

Or download a chime sound from a free sound library.
