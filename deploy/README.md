# Smart Home — Deployment

This directory contains everything needed to replicate the entire Smart Home
stack on a fresh Raspberry Pi 5 (or similar Debian Bookworm aarch64 device).

## Quick Start

```bash
# On a fresh Pi 5 with Raspberry Pi OS Bookworm (64-bit):
git clone https://github.com/alexanderleon255/Smart_Home.git ~/Smart_Home
cd ~/Smart_Home
./deploy/bootstrap.sh
```

The bootstrap script will:

1. Install system packages (Docker, PipeWire, build tools)
2. Install Ollama (local LLM runtime)
3. Create a Python virtualenv and install all dependencies
4. **Symlink** systemd user units from this directory into `~/.config/systemd/user/`
5. Enable linger (services start at boot without requiring login)
6. Start Docker containers (Home Assistant + Mosquitto)
7. Pull the default LLM model (`qwen2.5:1.5b`)
8. Enable and start all services
9. Optionally install Tailscale for sidecar LLM connectivity

## Systemd Units

All service definitions live in `deploy/systemd/` as the **single source of truth**.
The bootstrap script symlinks them into `~/.config/systemd/user/`, so edits to the
repo files are immediately picked up after `systemctl --user daemon-reload`.

| Unit | Type | Purpose |
|------|------|---------|
| `ollama.service` | simple | Ollama LLM server, bound to 0.0.0.0 |
| `tool-broker.service` | simple | FastAPI Tool Broker (port 8000) |
| `dashboard.service` | simple | Dash management dashboard (port 8050) |
| `jarvis-audio-devices.service` | oneshot | Creates PipeWire virtual audio sinks/sources |
| `sonobus.service` | simple | SonoBus headless audio bridge + wiring |

### Specifiers

The unit files use systemd `%h` (home directory) and `%E` (config directory)
specifiers instead of hard-coded paths, making them portable across usernames.

## Post-Bootstrap Configuration

Set these environment variables (in `~/.bashrc`, `.env`, or systemd overrides):

| Variable | Purpose | Example |
|----------|---------|---------|
| `HA_TOKEN` | Home Assistant long-lived access token | `eyJ0eX...` |
| `HA_URL` | Home Assistant URL (default: `http://localhost:8123`) | |
| `SIDECAR_OLLAMA_URL` | Mac sidecar Ollama URL | `http://100.98.1.21:11434` |
| `SIDECAR_OLLAMA_MODEL` | Sidecar model name | `llama3.1:8b` |
| `LLM_ROUTING_MODE` | `auto`, `local`, or `sidecar` | `auto` |

## Updating Services

After pulling new code:

```bash
cd ~/Smart_Home
git pull
systemctl --user daemon-reload   # picks up symlinked unit changes
systemctl --user restart tool-broker dashboard
```
