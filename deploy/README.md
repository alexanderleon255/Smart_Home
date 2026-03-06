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

## Backup & Restore

### Daily Backup

```bash
# Full backup (HA config, AI Context, Docker volumes, audit logs)
./deploy/backup.sh

# HA config only
./deploy/backup.sh --config-only

# Custom backup destination
BACKUP_DIR=/mnt/usb/backups ./deploy/backup.sh
```

Backups are stored as timestamped `.tar.gz` archives in `~/smart_home_backups/`
(override with `BACKUP_DIR`). Old backups are pruned after 30 days (override with
`BACKUP_RETENTION_DAYS`).

**Recommended cron schedule** (daily at 3 AM):

```bash
crontab -e
# Add:
0 3 * * * /home/pi/Smart_Home/deploy/backup.sh >> /var/log/smart_home_backup.log 2>&1
```

### What Gets Backed Up

| Component | Source | Archive Entry |
|-----------|--------|---------------|
| Home Assistant config | `../ha_config` (bind mount) | `ha_config.tar.gz` |
| AI Context | `AI_CONTEXT/` | `ai_context.tar.gz` |
| Mosquitto data | Docker volume `docker_mosquitto_data` | `mosquitto_data.tar.gz` |
| Pi-hole config | Docker volumes `docker_pihole_*` | `pihole_*.tar.gz` |
| Deploy configs | `deploy/` | `deploy.tar.gz` |
| Audit logs | `tool_broker/audit_*.jsonl` | `audit_logs.tar.gz` |

### Restore

```bash
# Extract to inspect
tar -xzf ~/smart_home_backups/backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/restore

# Restore HA config
tar -xzf /tmp/restore/backup_*/ha_config.tar.gz -C ~/Smart_Home/

# Restore Docker volume
docker run --rm -v docker_mosquitto_data:/data -v /tmp/restore/backup_*:/backup \
  alpine sh -c "cd /data && tar -xzf /backup/mosquitto_data.tar.gz"
```

## Updating Services

After pulling new code:

```bash
cd ~/Smart_Home
git pull
systemctl --user daemon-reload   # picks up symlinked unit changes
systemctl --user restart tool-broker dashboard
```
