# Operational Runbook

**Owner:** Alex  
**Created:** 2026-03-02  
**Status:** DRAFT - Placeholder

---

## 1. Overview

This document describes operational procedures for maintaining the Smart Home system.

| System | Location | Access |
|--------|----------|--------|
| Home Assistant | Pi 5 | `http://homeassistant.local:8123` |
| Ollama | Mac M1 | `http://localhost:11434` |
| Tool Broker | Mac M1 | `http://localhost:8000` |
| Zigbee2MQTT | Pi 5 | `http://homeassistant.local:8080` |

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
        <string>[TBD - path to python]</string>
        <string>[TBD - path to tool_broker/main.py]</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>[TBD - path to tool_broker]</string>
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
