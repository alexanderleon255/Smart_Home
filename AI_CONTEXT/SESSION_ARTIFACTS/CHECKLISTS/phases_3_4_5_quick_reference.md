# Phases 3-5: Quick Reference Checklists

**Purpose:** Condensed checklists for Voice, Security, and Camera phases.  
**Note:** For detailed implementation guidance, reference the master roadmap.

---

## Phase 3: Voice Pipeline

### P3-01: Voice Pipeline Add-ons
- [ ] Install Whisper add-on
- [ ] Install Piper add-on
- [ ] Install openWakeWord add-on
- [ ] Configure resource limits

### P3-02: Wake Word Configuration
- [ ] Select wake word model
- [ ] Configure sensitivity
- [ ] Test detection rate (>90%)
- [ ] Tune false positive rate (<5%)

### P3-03: Speech-to-Text Setup
- [ ] Select Whisper model (tiny/base/small)
- [ ] Test transcription accuracy
- [ ] Benchmark latency (<3s)
- [ ] Test with multiple speakers

### P3-04: Text-to-Speech Setup
- [ ] Select Piper voice
- [ ] Configure speed/pitch
- [ ] Test audio output
- [ ] Verify speaker config

### P3-05: Voice-to-Tool-Broker Integration
- [ ] Configure HA Assist for local STT
- [ ] Configure HA Assist for local TTS
- [ ] Create custom conversation agent
- [ ] Wire: voice → STT → Tool Broker → HA → TTS

### P3-06: Voice Command Testing
- [ ] Test 10+ commands
- [ ] Test noisy environment
- [ ] Test multiple speakers
- [ ] Document success rate (>90%)

---

## Phase 4: Security Hardening

### P4-01: Tailscale Installation
- [ ] Install on Pi 5
- [ ] Install on Mac M1
- [ ] Install on mobile devices
- [ ] Verify mesh connectivity

### P4-02: Tailscale ACLs
- [ ] Define ACL policy
- [ ] Admin → full access
- [ ] User → HA only
- [ ] Guest → no direct access
- [ ] Test restrictions

### P4-03: Local Firewall
- [ ] macOS firewall enabled
- [ ] Ollama LAN-only
- [ ] Pi 5 UFW configured
- [ ] Port scan verification

### P4-04: Credential Management
- [ ] Rotate default passwords
- [ ] Store in password manager
- [ ] Remove plaintext creds
- [ ] Document locations

### P4-05: Logging & Monitoring
- [ ] Enable HA logging
- [ ] Set 30-day retention
- [ ] Configure alerts (login, device join, errors)
- [ ] Test alert delivery

### P4-06: Security Audit
- [ ] External nmap scan (no ports)
- [ ] Test ACLs per device
- [ ] Verify tool whitelisting
- [ ] Verify entity validation
- [ ] Create audit report

---

## Phase 5: Camera Integration

### P5-01: Camera Selection
**Requirements:**
- RTSP support
- ONVIF compatible
- No mandatory cloud
- Local recording
- PoE preferred

- [ ] Research cameras
- [ ] Select model
- [ ] Acquire hardware

### P5-02: Camera Network Setup
- [ ] Connect camera
- [ ] Assign static IP
- [ ] Change admin password
- [ ] Disable cloud features
- [ ] Get RTSP URL

### P5-03: Home Assistant Integration
- [ ] Add via ONVIF/Generic Camera
- [ ] Verify live view
- [ ] Configure stream settings
- [ ] Add to dashboard

### P5-04: Motion Detection & Recording
- [ ] Enable motion detection
- [ ] Configure recording triggers
- [ ] Set up local storage
- [ ] Configure retention (7 days)
- [ ] Test sensitivity

### P5-05: Camera Security
- [ ] Isolate on IoT VLAN
- [ ] Block internet access
- [ ] Restrict to HA only
- [ ] Disable web interface
- [ ] Enable TLS if supported

---

## Hardware Decision Matrix

### Zigbee Dongles (DEC-001)
| Model | Price | Range | Notes |
|-------|-------|-------|-------|
| Sonoff ZBDongle-P | ~$15 | Good | Most popular |
| HUSBZB-1 | ~$40 | Good | Combo Zigbee+Z-Wave |
| ConBee II | ~$35 | Excellent | deCONZ required |

### Z-Wave Controllers (DEC-002)
| Model | Price | Gen | Notes |
|-------|-------|-----|-------|
| Zooz ZST10 700 | ~$30 | 700 | Latest gen |
| Aeotec Z-Stick 7 | ~$35 | 700 | Well-supported |

### LLM Models (DEC-003)
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| Llama 3 8B | 4.7GB | Fast | Better |
| Mistral 7B | 4.1GB | Faster | Good |

### Cameras (DEC-005)
| Brand | Pros | Cons |
|-------|------|------|
| Reolink | Affordable, RTSP | Some cloud features |
| Amcrest | Good value, local | Variable quality |
| Ubiquiti | Excellent quality | UniFi ecosystem required |

---

**END OF QUICK REFERENCE**
