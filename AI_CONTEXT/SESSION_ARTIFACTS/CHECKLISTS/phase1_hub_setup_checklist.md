# Phase 1: Hub Setup Implementation Checklist

**Initiative:** Raspberry Pi 5 Home Assistant Hub  
**Created:** 2026-03-02  
**Purpose:** Detailed task checklist for hub setup

---

## Pre-Implementation Checklist

### Hardware Required
- [ ] Raspberry Pi 5 (8GB RAM)
- [ ] NVMe HAT (e.g., Pimoroni NVMe Base, Argon ONE M.2)
- [ ] NVMe SSD (500GB+ recommended)
- [ ] USB-C power supply (5V/5A, 27W)
- [ ] Ethernet cable
- [ ] Zigbee USB dongle (see DEC-001)
- [ ] Z-Wave USB dongle (optional, see DEC-002)
- [ ] microSD card (for initial flashing, can reuse)

### Tools Required
- [ ] Another computer for flashing (Mac/PC)
- [ ] microSD card reader (if NVMe HAT doesn't support direct flash)
- [ ] Network access (same LAN as Mac)

---

## P1-01: Hardware Assembly

### Tasks
- [ ] Attach NVMe SSD to NVMe HAT
- [ ] Connect NVMe HAT to Pi 5
- [ ] Connect Ethernet cable to Pi 5
- [ ] DO NOT connect power yet

### Assembly Notes
```
NVMe HAT → Pi 5 GPIO/PCIe connector
Ethernet → Pi 5 ethernet port
USB-C power → Pi 5 USB-C port (last step)
```

### Verification
- [ ] NVMe SSD firmly seated
- [ ] HAT properly connected
- [ ] No loose connections

---

## P1-02: Home Assistant OS Installation

### Option A: Direct NVMe Flash (if HAT supports)
```bash
# Download HA OS image for Pi 5
# https://github.com/home-assistant/operating-system/releases
# File: haos_rpi5-64-XX.X.img.xz

# Flash using Raspberry Pi Imager
# Select: Home Assistant OS → Raspberry Pi 5
# Target: NVMe drive (via USB enclosure or HAT's flash mode)
```

### Option B: microSD Boot → NVMe Migration
```bash
# 1. Flash HA OS to microSD
# 2. Boot Pi 5 from microSD
# 3. Use HA Data Disk feature to migrate to NVMe
# 4. Remove microSD and reboot from NVMe
```

### Tasks
- [ ] Download latest HA OS for Pi 5
- [ ] Flash image to storage
- [ ] Insert/connect storage to Pi 5
- [ ] Connect power and boot
- [ ] Wait 5-10 minutes for first boot
- [ ] Access: `http://homeassistant.local:8123`
- [ ] Complete onboarding wizard
- [ ] Create admin account
- [ ] Enable MFA on admin account

### First Boot Checklist
- [ ] HA web UI accessible
- [ ] Admin account created (username: ______)
- [ ] Timezone configured
- [ ] Location configured (for sunrise/sunset)
- [ ] MFA enabled

---

## P1-03: Network Configuration

### Tasks
- [ ] Log into router admin panel
- [ ] Find Pi 5's current DHCP IP
- [ ] Create DHCP reservation (static IP)
- [ ] Document: Pi 5 IP = `192.168.X.X`
- [ ] Test access via IP: `http://192.168.X.X:8123`
- [ ] Test access via hostname: `http://homeassistant.local:8123`

### Network Documentation
```
Device: Raspberry Pi 5 (Home Assistant)
Hostname: homeassistant.local
IP Address: __________________
MAC Address: __________________
Gateway: __________________
DNS: __________________
```

### Optional: mDNS Setup
If `.local` resolution doesn't work on Mac:
```bash
# Test mDNS
dns-sd -B _home-assistant._tcp
```

---

## P1-04: Zigbee Coordinator Setup

### Hardware Decision (DEC-001)
| Option | Pros | Cons |
|--------|------|------|
| Sonoff ZBDongle-P | Popular, well-supported, cheap | USB 2.0 |
| HUSBZB-1 | Zigbee + Z-Wave combo | More expensive, older |
| ConBee II | Good range, deCONZ support | Needs deCONZ addon |

**Selected:** ________________

### Tasks
- [ ] Connect Zigbee dongle to Pi 5 USB port
- [ ] Install Zigbee2MQTT add-on:
  - Settings → Add-ons → Add-on Store → Zigbee2MQTT
- [ ] Configure Zigbee2MQTT:
  ```yaml
  # Configuration
  serial:
    port: /dev/ttyUSB0  # or /dev/ttyACM0
  ```
- [ ] Start Zigbee2MQTT add-on
- [ ] Access Z2M web UI (port 8080)
- [ ] Verify coordinator detected

### Test Device Pairing
- [ ] Put test device in pairing mode
- [ ] Enable "Permit Join" in Z2M
- [ ] Wait for device to appear
- [ ] Rename device appropriately
- [ ] Test device control from HA

### Troubleshooting
```bash
# Check USB devices (via SSH)
ls -la /dev/ttyUSB* /dev/ttyACM*

# Check Z2M logs
# Settings → Add-ons → Zigbee2MQTT → Logs
```

---

## P1-05: Z-Wave Coordinator Setup (OPTIONAL)

### Hardware Decision (DEC-002)
| Option | Pros | Cons |
|--------|------|------|
| Zooz ZST10 700 | Latest gen, good range | Higher price |
| Aeotec Z-Stick 7 | Well-supported | |
| Nortek HUSBZB-1 | Combo Zigbee+Z-Wave | Older, requires both addons |

**Selected:** ________________

### Tasks
- [ ] Connect Z-Wave dongle to Pi 5 USB port
- [ ] Install Z-Wave JS add-on:
  - Settings → Add-ons → Add-on Store → Z-Wave JS
- [ ] Configure Z-Wave JS:
  ```yaml
  serial:
    port: /dev/ttyUSB1  # Different from Zigbee
  ```
- [ ] Start Z-Wave JS add-on
- [ ] Complete Z-Wave network setup
- [ ] Pair test device

---

## P1-06: MQTT Broker Setup

### Tasks
- [ ] Install Mosquitto add-on:
  - Settings → Add-ons → Add-on Store → Mosquitto broker
- [ ] Configure authentication:
  ```yaml
  logins:
    - username: mqtt_user
      password: SECURE_PASSWORD_HERE
  ```
- [ ] Start Mosquitto add-on
- [ ] Configure Z2M to use MQTT broker:
  ```yaml
  mqtt:
    server: mqtt://homeassistant.local:1883
    user: mqtt_user
    password: SECURE_PASSWORD_HERE
  ```
- [ ] Verify MQTT integration appears in HA

### Test MQTT from Mac
```bash
# Install mosquitto client
brew install mosquitto

# Subscribe to all topics
mosquitto_sub -h homeassistant.local -p 1883 \
  -u mqtt_user -P PASSWORD -t '#'

# Publish test message
mosquitto_pub -h homeassistant.local -p 1883 \
  -u mqtt_user -P PASSWORD \
  -t 'test/topic' -m 'Hello MQTT'
```

---

## P1-07: Basic Automation Test

### Create Test Automation
```yaml
# Example: Turn on light at sunset
alias: "Sunset Light"
description: "Turn on living room light at sunset"
trigger:
  - platform: sun
    event: sunset
    offset: "-00:30:00"  # 30 min before sunset
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 50
mode: single
```

### Tasks
- [ ] Create automation via UI or YAML
- [ ] Test automation manually (Run action)
- [ ] Wait for trigger (or use Debug → Trigger)
- [ ] Verify action executed
- [ ] Check automation logs

### Verification
- [ ] Automation appears in Automations list
- [ ] Manual trigger works
- [ ] Logs show execution

---

## P1-08: Backup Configuration

### Tasks
- [ ] Settings → System → Backups
- [ ] Create manual backup (test)
- [ ] Download backup to Mac
- [ ] Enable automatic backups:
  - Install "Google Drive Backup" or "Samba Backup" add-on
  - OR: Configure external storage
- [ ] Set backup schedule (daily recommended)
- [ ] Set retention (keep 7 daily, 4 weekly)

### Test Restore (IMPORTANT)
- [ ] Create backup
- [ ] Note current configuration
- [ ] Restore backup
- [ ] Verify configuration intact

### Backup Locations
```
Local: /backup/ (HA internal)
External: _________________
Cloud: _________________
```

---

## Completion Checklist

- [ ] All P1 items complete
- [ ] HA running stable on NVMe
- [ ] At least one Zigbee device paired
- [ ] MQTT broker operational
- [ ] Basic automation working
- [ ] Backups configured
- [ ] Network documentation complete
- [ ] Progress tracker updated

---

## Network Documentation Template

```
=== SMART HOME NETWORK DOCUMENTATION ===

PRIMARY HUB
  Device: Raspberry Pi 5 (8GB)
  Hostname: homeassistant.local
  IP: 
  MAC: 

SERVICES
  Home Assistant: http://<IP>:8123
  Zigbee2MQTT: http://<IP>:8080
  MQTT Broker: mqtt://<IP>:1883

CREDENTIALS (stored in password manager)
  HA Admin: 
  MQTT User: 
  Z2M Admin: 

ZIGBEE DEVICES
  Coordinator: 
  Devices:
    - 
    - 

Z-WAVE DEVICES (if applicable)
  Controller: 
  Devices:
    - 
    - 
```

---

**END OF CHECKLIST**
