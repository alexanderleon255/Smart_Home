# Audio Routing Architecture — Raspberry Pi 5

> **Replaces:** macOS-centric audio routing (BlackHole + avfoundation)  
> **Date:** 2026-03-04  
> **Platform:** Raspberry Pi 5 (aarch64), PipeWire 1.4.2, SonoBus (built from source)

---

## Overview

The Pi has no built-in microphone or speakers suitable for voice interaction.
Audio I/O is handled remotely via **AirPods** connected to an Apple device
(iPhone, iPad, or MacBook), bridged to the Pi through **SonoBus** over
**Tailscale**.

PipeWire virtual devices replace macOS BlackHole as the internal routing layer.

---

## Audio Flow Diagram

```
INPUT PATH  (User voice -> Assistant):
  AirPods Mic -> iPhone/Mac/iPad -> SonoBus App
    -> Tailscale mesh -> Pi SonoBus (headless, pw-jack shim)
    -> alsa_playback.sonobus:output_FL/FR
    -> jarvis-mic-source:input_FL/FR
    -> ffmpeg -f pulse -i jarvis-mic-source -> whisper.cpp STT

OUTPUT PATH (Assistant voice -> User):
  Ollama LLM -> Piper TTS -> ffplay (PULSE_SINK=jarvis-tts-sink)
    -> jarvis-tts-sink:monitor_FL/FR
    -> alsa_capture.sonobus:input_FL/FR
    -> SonoBus network -> iPhone/Mac/iPad -> AirPods speakers
```

---

## PipeWire Virtual Devices

Two virtual audio nodes are created persistently via:  
`~/.config/pipewire/pipewire.conf.d/jarvis-virtual-devices.conf`

| Device | PulseAudio Name | Type | Sample Rate | Purpose |
|--------|----------------|------|-------------|---------|
| TTS Sink | `jarvis-tts-sink` | Audio/Sink | 22050 Hz | Piper TTS output target |
| TTS Monitor | `jarvis-tts-sink.monitor` | Source | 22050 Hz | Feed to SonoBus + recording |
| Virtual Mic | `jarvis-mic-source` | Audio/Source/Virtual | 16000 Hz | AirPods mic via SonoBus |

These replace macOS BlackHole 2ch + Audio MIDI Setup Multi-Output Device.

### Verify devices

```bash
pactl list sinks short    # should show jarvis-tts-sink
pactl list sources short  # should show jarvis-mic-source + jarvis-tts-sink.monitor
```

### Restart after config change

```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

---

## SonoBus Setup

### Key Discovery: PipeWire JACK Shim

SonoBus uses JUCE, which `dlopen()`s libjack at runtime. On the Pi, the
system libjack (jackd2) tries to connect to a JACK server that doesn't exist.

**Solution:** Launch SonoBus with `LD_LIBRARY_PATH` pointing to PipeWire's
JACK compatibility library. This makes JUCE load PipeWire's libjack shim
instead, routing all audio through PipeWire.

```bash
LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack \
    sonobus --headless -g jarvis-audio -n jarvis-pi
```

SonoBus then registers as PipeWire nodes:
- `alsa_playback.sonobus` (Stream/Output/Audio) — network audio FROM peers
- `alsa_capture.sonobus` (Stream/Input/Audio) — audio TO send to peers

### Pi (Server / Headless)

SonoBus is built from source for ARM64:

```bash
cd ~/sonobus/linux
./deb_get_prereqs.sh
./build.sh
sudo ./install.sh
# Binary: /usr/local/bin/sonobus (25MB, aarch64)
```

Required PipeWire packages:
```bash
sudo apt-get install -y pipewire-jack pipewire-alsa pulseaudio-utils
```

Launch headless (no display required):

```bash
./jarvis_audio/scripts/launch_jarvis_audio.sh [group-name]
# Default group: jarvis-audio
```

### iPhone / iPad / Mac (Client)

1. Install **SonoBus** from App Store (free)
2. Open SonoBus
3. Tap **Connect** -> enter group name: `jarvis-audio`
4. Audio Quality: **Best** (lowest latency)
5. On iPhone: Input = iPhone Mic, Output = AirPods
6. Ensure **Tailscale** is running if not on same LAN

### Tailscale Connection

When not on the same LAN, SonoBus peers find each other through the
SonoBus public connection server (aoo.sonobus.net). As long as both
devices have Tailscale active, the peer-to-peer audio stream routes
through the Tailscale mesh automatically.

| Device | Tailscale IP |
|--------|-------------|
| Pi 5 | 100.83.1.2 |
| MacBook Air | 100.98.1.21 |
| iPhone | 100.83.74.23 |

---

## Audio Wiring (pw-link)

After SonoBus is running and connected to a group, audio links are
established via `pw-link` using port IDs (to handle duplicate node names):

```
# Network audio -> Virtual mic (for Whisper STT)
pw-link alsa_playback.sonobus:output_FL  jarvis-mic-source:input_FL
pw-link alsa_playback.sonobus:output_FR  jarvis-mic-source:input_FR

# TTS output -> SonoBus -> AirPods
pw-link jarvis-tts-sink:monitor_FL  alsa_capture.sonobus:input_FL
pw-link jarvis-tts-sink:monitor_FR  alsa_capture.sonobus:input_FR
```

**HDMI cleanup:** WirePlumber auto-links SonoBus to HDMI. The wiring
script disconnects these unwanted links.

The `wire_sonobus.sh` script automates all wiring:

```bash
./jarvis_audio/scripts/wire_sonobus.sh
```

---

## Application Device Mapping

| Application | Reads From | Writes To |
|-------------|-----------|-----------|
| Piper TTS | -- | `jarvis-tts-sink` (via `PULSE_SINK`) |
| ffmpeg (STT) | `jarvis-mic-source` (via `-f pulse -i jarvis-mic-source`) | temp WAV file |
| ffmpeg (recording) | `jarvis-tts-sink.monitor` | session WAV file |
| SonoBus capture | `jarvis-tts-sink.monitor` | network (to remote peers) |
| SonoBus playback | network (from remote peers) | `jarvis-mic-source` |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `JARVIS_MIC_DEVICE` | `jarvis-mic-source` | PulseAudio source for STT input |
| `JARVIS_TTS_SINK` | `jarvis-tts-sink` | PulseAudio sink for TTS output |
| `JARVIS_RECORD_DEVICE` | `jarvis-tts-sink.monitor` | PulseAudio source for recording |
| `SONOBUS_GROUP` | `jarvis-audio` | SonoBus group name |
| `SONOBUS_BIN` | `/usr/local/bin/sonobus` | Path to SonoBus binary |

---

## Testing

### Test 1: TTS -> Virtual Sink -> SonoBus

```bash
echo "Hello from Jarvis" | ~/.local/piper/piper/piper \
  --model ~/.local/piper/models/en_US-lessac-medium.onnx \
  --output_raw | \
  PULSE_SINK=jarvis-tts-sink ffplay -f s16le -ar 22050 -ch_layout mono \
  -autoexit -nodisp - 2>/dev/null
```

### Test 2: Record from Virtual Mic

```bash
# Record 5 seconds from the virtual mic (silent unless SonoBus peer is sending)
pw-record --target=jarvis-mic-source /tmp/test_mic.wav
# Or:
ffmpeg -f pulse -i jarvis-mic-source -t 5 -ar 16000 -ac 1 /tmp/test_mic.wav -y
```

### Test 3: Full End-to-End

1. Start audio subsystem: `./jarvis_audio/scripts/launch_jarvis_audio.sh`
2. Connect iPhone SonoBus to group `jarvis-audio`
3. Wire audio: `./jarvis_audio/scripts/wire_sonobus.sh`
4. Speak into AirPods -- should appear in: `ffmpeg -f pulse -i jarvis-mic-source ...`
5. Play TTS -- should be heard in AirPods

---

## Troubleshooting

**SonoBus ports don't appear in PipeWire**
- Must launch with PipeWire JACK shim: `LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack sonobus --headless ...`
- Check: `pw-link -o | grep sonobus` (should show `alsa_playback.sonobus` and `alsa_capture.sonobus`)
- Verify pipewire-jack installed: `dpkg -l | grep pipewire-jack`

**JACK errors: "Cannot connect to server socket"**
- Normal when launching without `LD_LIBRARY_PATH` -- system libjack tries real JACK server
- Solution: use the launch script or set `LD_LIBRARY_PATH` as shown above

**No audio from AirPods in virtual mic**
- Check SonoBus on iPhone is connected to correct group
- Run `pw-link -l | grep sonobus` to verify links exist
- Re-run `./jarvis_audio/scripts/wire_sonobus.sh`

**TTS not heard in AirPods**
- Verify TTS writes to correct sink: `PULSE_SINK=jarvis-tts-sink`
- Check SonoBus reads from monitor: `pw-link -l | grep monitor`

**SonoBus wired to HDMI instead of Jarvis devices**
- WirePlumber auto-links SonoBus to HDMI on startup
- Run `./jarvis_audio/scripts/wire_sonobus.sh` which disconnects HDMI links

**High latency**
- Use SonoBus "Best" quality setting (lower = more latency)
- Use wired Ethernet if possible
- Target: <100ms round-trip

**PipeWire devices missing after reboot**
- Verify config: `cat ~/.config/pipewire/pipewire.conf.d/jarvis-virtual-devices.conf`
- Restart: `systemctl --user restart pipewire pipewire-pulse wireplumber`
