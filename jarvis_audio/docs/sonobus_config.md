# SonoBus Configuration Guide (P6-01)

## Overview

SonoBus provides low-latency bidirectional audio streaming between iPhone and Mac over local network or Tailscale VPN.

## Installation

### Mac
```bash
brew install --cask sonobus
```

### iPhone
Install SonoBus from App Store: https://apps.apple.com/app/sonobus/id1548608615

## Configuration

### Step 1: Network Setup

**Option A: Local Network (Simple)**
- Connect both devices to same WiFi
- Lower latency (~50ms)
- Only works at home

**Option B: Tailscale VPN (Recommended)**
- Works anywhere
- Secure encrypted tunnel
- Slightly higher latency (~100ms)
- Setup: Install Tailscale on both devices

### Step 2: SonoBus Settings

**On Mac:**
1. Open SonoBus
2. Click "Connect to Server" → "Use Direct Connect"
3. Group Name: `jarvis-audio`
4. Audio Quality: **Best** (lowest latency)
5. Input Device: `Built-in Microphone` or `SonoBus` (from iPhone)
6. Output Device: `Multi-Output Device` (includes BlackHole)
7. Click "Connect"

**On iPhone:**
1. Open SonoBus
2. Tap "Connect"
3. Group Name: `jarvis-audio` (same as Mac)
4. Quality: **Best**
5. Tap "Connect"

### Step 3: Audio Routing

```
iPhone Mic → SonoBus → Mac (receives audio from AirPods)
Mac TTS → BlackHole → SonoBus → iPhone → AirPods
```

## Testing

1. On Mac: `say "Testing audio"`
2. Should hear in AirPods via iPhone
3. Speak into AirPods → should see levels in Mac SonoBus

## Performance Tuning

| Setting | Value | Why |
|---------|-------|-----|
| Buffer Size | 128 samples | Lower latency |
| Audio Quality | Best | Highest fidelity |
| Jitter Buffer | Auto | Handles network variance |
| Send Channels | Stereo | Full audio quality |

## Troubleshooting

**High Latency (>200ms)**
- Check network connection
- Reduce buffer size
- Use local network instead of VPN

**Audio Dropouts**
- Increase jitter buffer
- Check CPU usage
- Close other audio apps

**No Audio**
- Verify AirPods connected to iPhone
- Check SonoBus input/output devices
- Verify both devices in same group

## Security

- Use Tailscale for remote access (encrypted)
- Never use public WiFi without VPN
- Direct connect mode (no cloud servers)

## Acceptance Criteria (P6-01)

- [x] Audio from iPhone mic reaches Mac
- [x] Audio from Mac reaches iPhone/AirPods
- [x] Latency < 100ms
- [x] Reliable connection over Tailscale
