# Operational Runbook

**Owner:** Alex  
**Created:** 2026-03-02  
**Last Updated:** 2026-03-07 (Rev 2.0 — Corrected for DEC-009/010/011/014: Pi-primary architecture)  
**Status:** ACTIVE

---

## 1. Overview

This document describes operational procedures for maintaining the Smart Home system.

| System | Host | Access |
|--------|------|--------|
| Home Assistant | Pi 5 (Docker) | `http://100.83.1.2:8123` or `homeassistant.local:8123` |
| Tool Broker | Pi 5 (uvicorn) | `http://100.83.1.2:8000` |
| Ollama (local) | Pi 5 | `http://100.83.1.2:11434` (qwen2.5:1.5b) |
| Ollama (sidecar) | Mac M1 | `http://100.98.1.21:11434` (llama3.1:8b) |
| Dashboard | Pi 5 (Dash) | `http://100.83.1.2:8050` |
| Mosquitto MQTT | Pi 5 (Docker) | `100.83.1.2:1883` |
| PipeWire | Pi 5 | System service |
| Tailscale | Pi + Mac + iPhone | Mesh VPN (no public ports) |

> **Architecture note (DEC-010/014):** The Pi runs Debian Bookworm (not HA OS) and hosts
> Tool Broker, local Ollama, Dashboard, and audio pipeline. The Mac is a sidecar
> for complex LLM queries only. All services persist via systemd user units.

---

## 2. Raspberry Pi Hub Operations

### 2.1 SSH Access

```bash
# Via Tailscale (preferred — works from anywhere on mesh)
ssh pi@100.83.1.2

# Via local network
ssh pi@homeassistant.local
```

### 2.2 Service Management (systemd user units)

All Smart Home services run as systemd user units under the `pi` user, with linger enabled for boot persistence.

```bash
# Check status of all services
systemctl --user status ollama tool-broker dashboard jarvis-audio-devices sonobus

# Restart a specific service
systemctl --user restart tool-broker

# View logs
journalctl --user -u tool-broker -f

# List all Smart Home units
systemctl --user list-units 'ollama*' 'tool-broker*' 'dashboard*' 'jarvis*' 'sonobus*'
```

| Unit | Description | Port |
|------|-------------|------|
| `ollama.service` | Local Ollama (qwen2.5:1.5b) | :11434 |
| `tool-broker.service` | FastAPI Tool Broker (uvicorn) | :8000 |
| `dashboard.service` | Dash management app | :8050 |
| `jarvis-audio-devices.service` | PipeWire virtual sink/source | — |
| `sonobus.service` | SonoBus headless audio bridge | — |

Unit files live in `deploy/systemd/`, symlinked to `~/.config/systemd/user/`.

### 2.3 Home Assistant (Docker)

HA runs as a Docker container, NOT HA OS. There is no `ha` CLI — use the REST API or web UI.

```bash
# Check HA container
docker ps --filter name=homeassistant

# View HA logs
docker logs homeassistant --tail 100 -f

# Restart HA
docker restart homeassistant

# HA config is bind-mounted from ../ha_config (relative to docker/ dir)
```

### 2.4 Health Check

```bash
# Quick health check — all services
curl -s http://localhost:8000/v1/health | python3 -m json.tool

# Individual checks
curl -s http://localhost:11434/api/tags     # Local Ollama
curl -s http://localhost:8123/api/           # HA (needs auth header)
curl -s http://localhost:8050/               # Dashboard
```

### 2.5 Reboot Procedures

```bash
# Graceful reboot (services auto-restart via systemd)
sudo reboot

# If a single service hangs
systemctl --user restart tool-broker
```

### 2.6 Log Access

```bash
# Tool Broker logs (including audit)
journalctl --user -u tool-broker --since "1 hour ago"

# HA logs
docker logs homeassistant --tail 200

# All Smart Home services
journalctl --user --since "1 hour ago"
```

---

## 3. Mac M1 Sidecar Operations

The Mac is a **sidecar only** — it hosts the llama3.1:8b model for complex queries routed via Tailscale. The Tool Broker does NOT run on the Mac.

### 3.1 Keep-Alive Configuration

**Problem:** Mac sleeps → sidecar LLM tier becomes unavailable (Tool Broker falls back to local qwen2.5:1.5b on Pi).

```bash
# Prevent sleep while on power
sudo pmset -c sleep 0
sudo pmset -c displaysleep 0

# Or use caffeinate for specific duration
caffeinate -d -i -s -u &
```

### 3.2 Ollama Management

```bash
# Check Ollama
curl -s http://localhost:11434/api/tags

# Restart
brew services restart ollama

# Ollama must listen on 0.0.0.0 for Tailscale access
# Set OLLAMA_HOST=0.0.0.0 in launch config
```

### 3.3 Sidecar Down — Impact

When the Mac is offline/asleep:
- Tool Broker health endpoint shows `"sidecar": "unreachable"`
- Complex queries get routed to local tier (lower quality but functional)
- All automations, dashboard, voice pipeline continue normally on Pi
- **No user action required** — the system is designed for graceful degradation

---

## 4. Backup Procedures

### 4.1 Automated Backup Script

```bash
# Run the backup script (on Pi)
~/Smart_Home/deploy/backup.sh

# What it backs up:
# - HA config (bind mount)
# - AI_CONTEXT/ (tar)
# - Docker volumes (mosquitto, pihole)
# - deploy/ configs
# - Audit logs
# - 30-day retention with automatic pruning

# Schedule via cron (daily at 2 AM):
# 0 2 * * * /home/pi/Smart_Home/deploy/backup.sh >> /var/log/smart_home_backup.log 2>&1
```

### 4.2 Manual HA Backup

HA is Docker-based, so backups are file-based:

```bash
# Stop HA, copy config, restart
docker stop homeassistant
tar -czf ha_config_$(date +%Y%m%d).tar.gz ../ha_config/
docker start homeassistant
```

### 4.3 AI Context Backup

```bash
tar -czf smart_home_ai_context_$(date +%Y%m%d).tar.gz AI_CONTEXT/
```

### 4.4 Restore Procedure

```bash
# Restore HA config
docker stop homeassistant
tar -xzf ha_config_YYYYMMDD.tar.gz -C ../
docker start homeassistant

# Restore AI Context
tar -xzf smart_home_ai_context_YYYYMMDD.tar.gz -C ~/Smart_Home/
```

---

## 5. Update Procedures

### 5.1 Home Assistant Updates

```bash
# Pull latest HA Docker image
docker pull ghcr.io/home-assistant/home-assistant:stable

# Recreate container (docker-compose)
cd ~/Smart_Home/docker && docker compose up -d
```

### 5.2 Ollama Updates (Pi)

```bash
# Ollama installed via install script on Pi
curl -fsSL https://ollama.com/install.sh | sh

# Re-pull model after update
ollama pull qwen2.5:1.5b
```

### 5.3 Ollama Updates (Mac)

```bash
brew upgrade ollama
brew services restart ollama
```

### 5.4 Tool Broker / Codebase Updates

```bash
cd ~/Smart_Home
git pull
.venv/bin/pip install -r requirements.txt
systemctl --user restart tool-broker dashboard
```

---

## 6. Monitoring & Alerts

### 6.1 What to Monitor

| Component | Check | Method |
|-----------|-------|--------|
| Tool Broker | Health endpoint | `curl localhost:8000/v1/health` |
| HA | Container running | `docker ps` |
| Local Ollama | API responsive | `curl localhost:11434/api/tags` |
| Sidecar Ollama | Reachable via Tailscale | `curl 100.98.1.21:11434/api/tags` |
| Disk Usage | < 80% | `df -h /` |
| CPU Temp | < 70°C | `cat /sys/class/thermal/thermal_zone0/temp` |

### 6.2 Security Monitor

```bash
# Run security monitor (deploy/security/security-monitor.sh)
~/Smart_Home/deploy/security/security-monitor.sh

# Checks: failed auth attempts, new Tailscale peers, automation errors
```

### 6.3 Security Audit

```bash
# Generate timestamped security audit report
~/Smart_Home/deploy/security/run-security-audit.sh
# Reports saved to AI_CONTEXT/SESSION_ARTIFACTS/SECURITY_AUDITS/
```

---

## 7. Incident Response

### 7.1 Common Issues

#### Tool Broker Not Responding
1. Check: `systemctl --user status tool-broker`
2. View logs: `journalctl --user -u tool-broker --since "10 min ago"`
3. Restart: `systemctl --user restart tool-broker`
4. Verify: `curl localhost:8000/v1/health`

#### LLM Not Responding (Local)
1. Check: `systemctl --user status ollama`
2. Test: `curl localhost:11434/api/tags`
3. Restart: `systemctl --user restart ollama`

#### LLM Not Responding (Sidecar)
1. Check Mac is awake and on Tailscale
2. Test from Pi: `curl 100.98.1.21:11434/api/tags`
3. On Mac: `brew services restart ollama`
4. **Note:** Local tier continues working — this is a degraded, not failed, state

#### HA Not Responding
1. Check: `docker ps --filter name=homeassistant`
2. Logs: `docker logs homeassistant --tail 50`
3. Restart: `docker restart homeassistant`

#### Audio Pipeline Issues
1. Check PipeWire: `pw-cli info all | head`
2. Check virtual devices: `pactl list sources short` / `pactl list sinks short`
3. Restart audio: `systemctl --user restart jarvis-audio-devices sonobus`
4. Re-wire SonoBus: `~/Smart_Home/jarvis_audio/scripts/wire_sonobus.sh`

### 7.2 Full System Recovery

1. SSH into Pi (or connect keyboard/monitor)
2. `systemctl --user restart ollama tool-broker dashboard jarvis-audio-devices sonobus`
3. `docker restart homeassistant`
4. Verify: `curl localhost:8000/v1/health`

### 7.3 Emergency Fallback

If everything fails:
- HA web UI still works at :8123 for manual device control
- Physical switches still work
- HA automations run independently of Tool Broker / LLM

---

## 8. Maintenance Schedule

### Daily (automated)
- Backup runs at 2 AM (`deploy/backup.sh` via cron)
- Audit log rotation (30-day retention, built into audit_log.py)

### Weekly
- Review security monitor output
- Check disk usage
- Verify sidecar reachability

### Monthly
- Check for HA Docker image updates
- Check for Ollama updates (Pi + Mac)
- Review and prune old backups beyond 30-day window
- Run `pytest tests/ -q` after any updates

### Quarterly
- Run formal security audit (`run-security-audit.sh`)
- Review Tailscale ACLs
- Test backup restore procedure

---

## 9. Quick Reference

| Resource | URL/Command |
|----------|-------------|
| HA Web UI | `http://100.83.1.2:8123` |
| Dashboard | `http://100.83.1.2:8050` |
| Tool Broker Health | `curl http://100.83.1.2:8000/v1/health` |
| Pi SSH | `ssh pi@100.83.1.2` |
| Run tests | `.venv/bin/python -m pytest tests/ -q` |
| Backup | `~/Smart_Home/deploy/backup.sh` |
| Security audit | `~/Smart_Home/deploy/security/run-security-audit.sh` |

---

## 10. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-02 | Initial creation (Mac-primary architecture) | Alex |
| 2026-03-07 | Rev 2.0 — Rewritten for Pi-primary architecture (DEC-009/010/011/014). Mac is sidecar only. systemd services, Docker HA, deploy/backup.sh, security tools. | AI |

---

**END OF DOCUMENT**

---

## 2. Mac M1 Sidecar Operations

### 2.1 Keep-Alive Configuration

**Problem:** Mac sleeps, closes lid, or is taken elsewhere → AI features stop working.

**Solutions:**

#### Option A: Prevent Sleep (While at Home)
```bash
# Prevent sleep while on power
sudo pmset -c sleep 0
sudo pmset -c displaysleep 0

# Or use caffeinate for specific duration
caffeinate -d -i -s -u &
```

#### Option B: Ollama as LaunchAgent (Auto-Start)
```xml
<!-- ~/Library/LaunchAgents/com.ollama.serve.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.serve</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
# Load the agent
launchctl load ~/Library/LaunchAgents/com.ollama.serve.plist
```

#### Option C: Tool Broker as LaunchAgent
```xml
<!-- ~/Library/LaunchAgents/com.smarthome.toolbroker.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.smarthome.toolbroker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/alexleon/Developer/BoltPatternSuiteV.1/.venv/bin/python</string>
        <string>/Users/alexleon/Developer/BoltPatternSuiteV.1/Smart_Home/tool_broker/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/alexleon/Developer/BoltPatternSuiteV.1/Smart_Home/tool_broker</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HA_TOKEN</key>
        <string>[STORED IN KEYCHAIN - see 2.2]</string>
    </dict>
</dict>
</plist>
```

### 2.2 Credential Management

**HA Token Storage (Keychain):**
```bash
# Store token
security add-generic-password -a "smarthome" -s "ha_token" -w "YOUR_TOKEN_HERE"

# Retrieve token (in Python)
import keyring
token = keyring.get_password("smarthome", "ha_token")
```

### 2.3 Health Check Script

```bash
#!/bin/bash
# check_ai_sidecar.sh

echo "=== AI Sidecar Health Check ==="
echo ""

# Check Ollama
echo "Ollama:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  ✅ Running"
    ollama list | head -3
else
    echo "  ❌ Not responding"
fi
echo ""

# Check Tool Broker
echo "Tool Broker:"
if curl -s http://localhost:8000/v1/health > /dev/null 2>&1; then
    echo "  ✅ Running"
    curl -s http://localhost:8000/v1/health | jq .
else
    echo "  ❌ Not responding"
fi
echo ""

# Check HA connectivity
echo "Home Assistant:"
if curl -s http://homeassistant.local:8123/api/ > /dev/null 2>&1; then
    echo "  ✅ Reachable"
else
    echo "  ❌ Not reachable"
fi
```

### 2.4 Restart Procedures

```bash
# Restart Ollama
brew services restart ollama
# OR
launchctl kickstart -k gui/$(id -u)/com.ollama.serve

# Restart Tool Broker
launchctl kickstart -k gui/$(id -u)/com.smarthome.toolbroker

# Full restart
brew services restart ollama
# Wait 10 seconds
sleep 10
# Then restart tool broker
```

---

## 3. Raspberry Pi Hub Operations

### 3.1 SSH Access

```bash
# SSH into Pi
ssh [user]@homeassistant.local
# OR
ssh [user]@[PI_IP_ADDRESS]
```

### 3.2 Home Assistant CLI

```bash
# In SSH session
ha core check         # Check config
ha core restart       # Restart HA
ha supervisor info    # Supervisor status
ha addons list        # List add-ons
ha backups list       # List backups
```

### 3.3 Reboot Procedures

```bash
# Graceful reboot via HA
ha host reboot

# Or via SSH
sudo reboot
```

### 3.4 Log Access

```bash
# View HA core logs
ha core logs

# View specific add-on logs
ha addons logs [addon_slug]

# Examples
ha addons logs core_mosquitto
ha addons logs a]_zigbee2mqtt
```

---

## 4. Backup Procedures

### 4.1 Home Assistant Backups

**Automatic Backups:**
- Configured in HA: Settings → System → Backups
- Schedule: Daily at 3:00 AM
- Retention: 7 daily, 4 weekly

**Manual Backup:**
1. HA UI → Settings → System → Backups
2. Click "Create Backup"
3. Select Full or Partial
4. Wait for completion
5. Download to external storage

**Backup Contents:**
- Configuration files
- Automations
- Scripts
- Integrations
- Add-on data
- Secrets (encrypted)

### 4.2 Off-Site Backup

**Option A: Samba Share**
- Configure Samba Backup add-on
- Point to NAS or Mac share
- Schedule: After HA backup

**Option B: Google Drive**
- Configure Google Drive Backup add-on
- Authenticate with Google
- Schedule automatic uploads

**Option C: Manual Download**
- Download backup from HA UI
- Store on external drive
- Store in cloud (encrypted)

### 4.3 Restore Procedure

1. Fresh HA install (or existing)
2. Settings → System → Backups
3. Upload backup file
4. Select "Restore"
5. Wait for completion (may take 10-30 min)
6. System will restart

### 4.4 AI Context Backup

```bash
# Backup AI context files
tar -czf smart_home_ai_context_$(date +%Y%m%d).tar.gz \
    Smart_Home/AI_CONTEXT/

# Store with HA backups or separately
```

---

## 5. Update Procedures

### 5.1 Home Assistant Updates

**Check for Updates:**
1. HA UI → Settings → System → Updates
2. Review release notes

**Update Process:**
1. Create backup BEFORE updating
2. Click "Update"
3. Wait for download and install
4. System will restart
5. Verify functionality

**Update Schedule:**
- Core: Monthly (after 1 week of release)
- OS: Quarterly
- Add-ons: As needed

### 5.2 Ollama Updates

```bash
# Check current version
ollama --version

# Update via Homebrew
brew upgrade ollama

# Restart service
brew services restart ollama
```

### 5.3 Model Updates

```bash
# Check for model updates
ollama list

# Pull latest version
ollama pull llama3:8b

# Remove old version (if needed)
ollama rm llama3:8b-old
```

### 5.4 Zigbee Firmware Updates

1. Check Z2M for coordinator updates
2. Backup configuration
3. Follow Z2M update procedure
4. Re-pair devices if necessary (usually not needed)

---

## 6. Monitoring & Alerts

### 6.1 What to Monitor

| Component | Check | Frequency |
|-----------|-------|-----------|
| HA Core | Running, accessible | Continuous |
| Ollama | API responsive | Every 5 min |
| Tool Broker | Health endpoint | Every 5 min |
| Zigbee | Coordinator online | Continuous |
| Disk Usage | < 80% | Daily |
| Memory | < 90% | Hourly |
| CPU Temp | < 70°C | Hourly |

### 6.2 Alert Configuration

**HA Notification Automation:**
```yaml
alias: "System Health Alert"
trigger:
  - platform: numeric_state
    entity_id: sensor.processor_temperature
    above: 70
action:
  - service: notify.mobile_app
    data:
      title: "⚠️ System Alert"
      message: "Pi CPU temperature is {{ states('sensor.processor_temperature') }}°C"
```

### 6.3 Daily Health Check

Run this checklist daily (or automate):

- [ ] HA web UI accessible
- [ ] Voice commands working
- [ ] All lights responding
- [ ] Thermostat connected
- [ ] No error notifications
- [ ] Disk usage OK
- [ ] Backup completed

---

## 7. Incident Response

### 7.1 Common Issues

#### AI Not Responding
1. Check Mac awake: `pmset -g`
2. Check Ollama: `curl http://localhost:11434/api/tags`
3. Check Tool Broker: `curl http://localhost:8000/v1/health`
4. Restart services if needed

#### Device Not Responding
1. Check HA entity state
2. Check Z2M device status
3. Try toggling from HA UI
4. Re-pair device if needed
5. Check device battery (if applicable)

#### Automation Not Running
1. Check automation enabled
2. Check trigger conditions
3. Review automation trace
4. Check entity availability
5. Review logs for errors

#### Network Connectivity Lost
1. Check router status
2. Verify Pi has IP
3. Verify Mac has IP
4. Check Tailscale status
5. Restart networking if needed

### 7.2 Recovery Procedures

#### Full System Recovery (Pi)
1. Boot from backup SD card (emergency)
2. OR: Fresh HA install
3. Restore from backup
4. Reconfigure network
5. Verify all integrations

#### LLM Recovery (Mac)
1. Reinstall Ollama: `brew reinstall ollama`
2. Re-pull model: `ollama pull llama3:8b`
3. Restart services
4. Test with simple query

---

## 8. Maintenance Schedule

### Daily
- [ ] Verify voice commands work
- [ ] Check for error notifications
- [ ] Review automation logs

### Weekly
- [ ] Download backup to external location
- [ ] Check disk usage
- [ ] Review security logs
- [ ] Test remote access

### Monthly
- [ ] Review HA updates
- [ ] Update Ollama if available
- [ ] Clean up old logs
- [ ] Review automation performance
- [ ] Check all devices responding

### Quarterly
- [ ] Full system backup test (restore to test env)
- [ ] Review security settings
- [ ] Update Tailscale ACLs if needed
- [ ] Review and prune unused entities
- [ ] Performance optimization

---

## 9. Contact & Resources

### Quick Reference

| Resource | URL/Command |
|----------|-------------|
| HA Community | community.home-assistant.io |
| HA Documentation | home-assistant.io/docs |
| Ollama Documentation | ollama.ai/docs |
| Zigbee2MQTT Docs | zigbee2mqtt.io |

### Emergency Fallback

If AI system completely fails:
1. HA web UI still works for manual control
2. Physical switches still work
3. Most devices have manual fallback
4. Core automations run independently of AI

---

## 10. Runbook Updates

**When to Update:**
- After any system change
- After resolving an incident
- When adding new components
- Quarterly review

**Change Log:**
| Date | Change | Author |
|------|--------|--------|
| 2026-03-02 | Initial creation | Alex |

---

**END OF DOCUMENT**
