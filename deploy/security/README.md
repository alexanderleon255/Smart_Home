# Smart Home — Security Hardening

**Roadmap:** P4-02 (Tailscale ACLs), P4-03 (Local Firewall)  
**Reference:** `References/Smart_Home_Threat_Model_Analysis_Rev_1_0.md`

---

## Overview

Three layers of network security:

1. **Tailscale ACLs** — Control which tailnet devices can reach which ports
2. **Pi Firewall (UFW)** — OS-level packet filtering on the Pi 5
3. **Mac Firewall (pf)** — OS-level packet filtering on Mac M1 sidecar

## Files

| File | Purpose | Run On |
|------|---------|--------|
| `tailscale-acl-policy.jsonc` | Tailscale ACL policy (paste into admin console) | Tailscale admin UI |
| `setup-firewall-pi.sh` | UFW firewall setup for Pi 5 | Pi 5 (`sudo`) |
| `setup-firewall-mac.sh` | pf + Application Firewall for Mac M1 | Mac (`sudo`) |
| `verify-security.sh` | Verify security posture from any device | Any host |

## Port Inventory

### Pi 5 (100.83.1.2)

| Port | Protocol | Service | Access |
|------|----------|---------|--------|
| 22 | TCP | SSH | Admin only (rate-limited) |
| 1883 | TCP | MQTT (Mosquitto) | Localhost + Docker + Tailscale |
| 8000 | TCP | Tool Broker (FastAPI) | LAN + Tailscale |
| 8050 | TCP | Dashboard (Dash) | LAN + Tailscale |
| 8123 | TCP | Home Assistant | LAN + Tailscale |
| 10998 | UDP | SonoBus (audio bridge) | LAN + Tailscale |
| 11434 | TCP | Ollama (local LLM) | LAN + Tailscale |

### Mac M1 (100.98.1.21)

| Port | Protocol | Service | Access |
|------|----------|---------|--------|
| 11434 | TCP | Ollama (sidecar LLM) | LAN + Tailscale |

## Deployment Steps

### Step 1: Apply Tailscale ACLs

1. Open <https://login.tailscale.com/admin/acls>
2. Copy contents of `tailscale-acl-policy.jsonc`
3. Paste and click **Save** (Tailscale auto-validates the built-in tests)
4. Assign device tags in <https://login.tailscale.com/admin/machines>:
   - Pi 5 → `tag:server`
   - Mac M1 → `tag:sidecar`
   - iPhone → `tag:mobile`
   - iPad → `tag:mobile`

### Step 2: Pi Firewall

```bash
# SSH to Pi first, then:
cd ~/Smart_Home
sudo ./deploy/security/setup-firewall-pi.sh

# IMPORTANT: Verify SSH still works before closing your session!
# Open a NEW SSH session to the Pi to confirm access.
```

### Step 3: Mac Firewall

```bash
cd ~/Developer/Smart_Home
sudo ./deploy/security/setup-firewall-mac.sh

# Verify Ollama is still reachable from Pi:
# (from Pi) curl -s http://100.98.1.21:11434/api/tags
```

### Step 4: Verify

```bash
# From any device on the tailnet:
./deploy/security/verify-security.sh

# Or specific checks:
./deploy/security/verify-security.sh --tailscale
./deploy/security/verify-security.sh --pi-only
./deploy/security/verify-security.sh --mac-only
```

## Tailscale ACL Design

### Device Tiers

| Tag | Devices | Access Level |
|-----|---------|--------------|
| `tag:server` | Pi 5 | Hub — all services hosted here |
| `tag:sidecar` | Mac M1 | AI sidecar — Ollama only |
| `tag:mobile` | iPhone, iPad | User-facing services only |
| `tag:admin` | (future) | Dedicated admin device |
| `tag:guest` | (future) | No tailnet access |

### Access Matrix

| Source → Dest | Pi SSH | Pi HA | Pi Broker | Pi Dashboard | Pi Ollama | Pi MQTT | Mac Ollama |
|---|---|---|---|---|---|---|---|
| **Admin (Alex)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Mobile (iPhone/iPad)** | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Sidecar (Mac)** | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | — |
| **Pi → Mac** | ❌ | — | — | — | — | — | ✅ |
| **Users (partner)** | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Guest** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Rollback

### Pi Firewall
```bash
sudo ufw disable
sudo ufw reset
```

### Mac Firewall
```bash
sudo pfctl -d
sudo cp /etc/pf.conf.bak.smart_home /etc/pf.conf
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### Tailscale ACLs
Replace the ACL policy in the admin console with an empty/default policy.

## Maintenance

- **Quarterly:** Review Tailscale device list, remove stale devices
- **Quarterly:** Review UFW rules (`sudo ufw status numbered`)
- **On device change:** Update ACL tags in Tailscale admin console
- **On new service:** Add port to both UFW rules and this README
