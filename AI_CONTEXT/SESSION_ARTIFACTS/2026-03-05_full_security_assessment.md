# Smart Home — Full Security Assessment

**Date:** 2026-03-05  
**Assessor:** AI Agent (Claude Opus 4.6 via GitHub Copilot)  
**Scope:** Everything — Mac, Pi, router, WiFi, network, services, Tailscale, and Smart Home application stack  
**Assessment Type:** Comprehensive posture review for a new home automation operator  

---

## TL;DR — Your Security at a Glance

| Area | Grade | Verdict |
|------|-------|---------|
| **Tailscale / Remote Access** | A | Solid. No public ports. Encrypted mesh. |
| **macOS Core Security** | B+ | FileVault ON, SIP ON, Gatekeeper ON. But firewall is OFF and SSH is ON. |
| **macOS Exposed Services** | C- | 9 ports bound to all interfaces (not just localhost). Several shouldn't be. |
| **WiFi Network** | B- | WPA2 Personal — adequate but upgradeable to WPA3. |
| **Router / Gateway** | ? | Could not audit — requires manual checks (see below). |
| **Smart Home Application** | B+ | API key auth, PolicyGate, entity validation, tool whitelisting. Shell injection bugs remain. |
| **Pi 5 Firewall** | ⬜ | Script created but not yet applied. |
| **Mac Firewall** | ⬜ | Script created but not yet applied. Firewall currently **OFF**. |
| **Physical Security** | ? | Cannot audit remotely. |

---

## 1. What I Found On Your Mac

### 1.1 Operating System

| Check | Status | Notes |
|-------|--------|-------|
| macOS version | macOS 26.1 (Build 25B78) | ✅ Current |
| Auto-update | ON | ✅ Good |
| FileVault (disk encryption) | **ON** | ✅ Excellent — if your Mac is stolen, data is encrypted |
| System Integrity Protection | **Enabled** | ✅ Prevents malware from modifying system files |
| Gatekeeper | **Enabled** | ✅ Only signed/notarized apps can run |

**Verdict:** Your macOS core security is solid.

### 1.2 macOS Firewall — ⚠️ PROBLEM

| Check | Status | Notes |
|-------|--------|-------|
| Application Firewall | **OFF** | ❌ Not protecting you |
| Stealth Mode | **OFF** | ❌ Your Mac responds to port scans and pings |

**What this means:** Right now, any device on your WiFi network can connect to any open port on your Mac. This includes Ollama (your LLM), the Tool Broker, and several other services.

**Fix:** Run the Mac firewall script we created:
```bash
sudo ./deploy/security/setup-firewall-mac.sh
```

### 1.3 Ports Open to Your Entire Network — ⚠️ CONCERN

These services are listening on `*` (all network interfaces), meaning any device on your WiFi can reach them:

| Port | Service | Should It Be Open? | Risk |
|------|---------|---------------------|------|
| **8000** | Tool Broker (Python/uvicorn) | Only to LAN+Tailscale | Medium — has API key auth, but still |
| **11434** | Ollama (LLM server) | Only to LAN+Tailscale | Medium — no auth at all on Ollama |
| **5000** | AirPlay Receiver (ControlCenter) | Probably fine | Low — Apple service |
| **7000** | AirPlay Receiver (ControlCenter) | Probably fine | Low — Apple service |
| **3689** | Media Sharing (iTunes/Music DAAP) | Do you use this? | Low — if not, disable it |
| **13618** | BambuStudio (3D printer) | Do you use a Bambu printer? | Low — if yes, expected |
| **37434, 37878** | Tailscale (IPNExtension) | Yes, needed | ✅ Expected |
| **63086** | rapportd (AirDrop/Handoff) | Apple system service | Low |

**Key concerns:**
- **Ollama on `*:11434`** has **zero authentication**. Anyone on your WiFi can send prompts to your LLM. Not dangerous per se, but it's an unnecessary exposure.
- **Tool Broker on `*:8000`** has API key auth, which helps, but binding to all interfaces when only LAN+Tailscale is needed is overly broad.

### 1.4 Remote Login (SSH) — ⚠️ REVIEW NEEDED

| Check | Status | Notes |
|-------|--------|-------|
| Remote Login (SSH) | **ON** | Anyone on your WiFi can attempt SSH to your Mac |

**Question:** Do you actively SSH into your Mac from other devices? If not, turn it off:
- System Settings → General → Sharing → Remote Login → OFF

If you do need it, it's fine — macOS requires your account password. But with the firewall OFF, it's exposed to every device on your WiFi.

### 1.5 Other Observations

| Check | Status | Notes |
|-------|--------|-------|
| Remote Management (ARD) | Running | Apple Remote Management agent is active |
| RealVNC Viewer | Running | VNC client is installed and running |
| Bluetooth | Could not check | Needs manual verification |

---

## 2. Your WiFi Network

### 2.1 WiFi Security

| Check | Status | Notes |
|-------|--------|-------|
| Security Protocol | **WPA2 Personal** | ⚠️ Adequate but not ideal |
| Band | 5GHz, 80MHz channel | ✅ Good — 5GHz is harder to sniff from far away |
| PHY Mode | 802.11ac | ✅ |
| WiFi Mac Address | d4:57:63:c7:de:d7 | — |

**WPA2 Personal vs WPA3:**
- WPA2 Personal uses a shared password. It's been the standard for 15+ years and is "fine" for most people.
- **WPA3 Personal** adds protection against offline password cracking (SAE handshake) and forward secrecy. If your router supports it, switch to WPA3 or WPA2/WPA3 transitional mode.
- Your Mac supports 802.11ax (WiFi 6) which means it can do WPA3. Check if your router can too.

### 2.2 Network Layout

| Device | IP | Connection |
|--------|-----|-----------|
| Mac M1 | 192.168.0.119 | WiFi |
| Pi 5 | 192.168.0.189 | WiFi (or Ethernet?) |
| Router/Gateway | 192.168.0.1 | — |
| DNS | 100.100.100.100 (Tailscale) + 192.168.0.1 | — |
| Public IP | 172.56.120.160 | — |
| Subnet | 255.255.255.0 (/24) | — |

**DNS observation:** Your primary DNS goes through Tailscale's DNS (100.100.100.100), which is good — it means MagicDNS is working and your DNS queries are encrypted through Tailscale. Your fallback is your router's DNS (192.168.0.1), which your router likely forwards to your ISP.

**Public IP observation:** 172.56.x.x is a T-Mobile/home ISP range. This is your external-facing IP. As long as you have no port forwarding rules, nothing inside your network is reachable from the internet.

---

## 3. Your Router — ❓ Cannot Audit Remotely

I cannot access your router's admin interface programmatically (which is correct — it should require a password). But the router is **the most important security device in your home**. Here's what you need to check manually:

### 3.1 Critical Router Checks (Do These Today)

| # | Check | Why | How |
|---|-------|-----|-----|
| 1 | **Change default admin password** | Default passwords are published online. Anyone on your WiFi (or sometimes from the internet) can reconfigure your router. | Open http://192.168.0.1 in your browser. Log in. Change the admin password to something long and random. |
| 2 | **Disable UPnP** | UPnP allows any device on your network to automatically open ports to the internet. Malware uses this to expose your network. | Router admin → Advanced/NAT settings → UPnP → **OFF** |
| 3 | **Disable WPS (WiFi Protected Setup)** | WPS has a known brute-force vulnerability. An attacker within WiFi range can crack the PIN. | Router admin → WiFi settings → WPS → **OFF** |
| 4 | **Check port forwarding rules** | If anything is forwarded, your Pi or Mac could be reachable from the internet. | Router admin → NAT / Port Forwarding → should show **no rules** |
| 5 | **Disable remote management** | Some routers allow admin access from the internet. This should be OFF. | Router admin → Administration → Remote Management → **OFF** |
| 6 | **Update router firmware** | Routers get security patches. Most people never update them. | Router admin → Firmware Update → check for updates |

### 3.2 Recommended Router Improvements (Do When You Can)

| # | Improvement | Why | Difficulty |
|---|-------------|-----|------------|
| 1 | **Upgrade to WPA3** (if router supports it) | Better WiFi encryption | Easy — WiFi settings |
| 2 | **Set up a guest WiFi network** | Isolate visitors' devices from your smart home devices | Easy — most routers have this |
| 3 | **Use a strong WiFi password** | 16+ character random passphrase | Easy — change in WiFi settings |
| 4 | **Create IoT VLAN** (if router supports it) | When you add Zigbee/Z-Wave devices, isolate them so a compromised bulb can't reach your Mac | Medium — requires VLAN-capable router |
| 5 | **Switch to a DNS provider** like NextDNS or Cloudflare (1.1.1.1) | Block ads, malware domains, and get encrypted DNS | Easy — change DNS in router settings |
| 6 | **Consider a better router** | Consumer routers from ISPs are notoriously insecure and rarely updated | Varies — Ubiquiti, pfSense, or even a good ASUS router with Merlin firmware |

### 3.3 How to Identify Your Router

Open http://192.168.0.1 in your browser. The login page usually shows the brand/model. Common home setups:
- **ISP-provided** (Xfinity, AT&T, T-Mobile Home Internet) — often limited settings, harder to secure
- **Consumer router** (ASUS, Netgear, TP-Link, Linksys) — more configurable
- **Prosumer** (Ubiquiti UniFi, pfSense, Firewalla) — full control, VLAN support

Tell me what you find and I can give specific guidance for your router model.

---

## 4. Tailscale Network

### 4.1 Tailscale Peers

| Device | Tailscale IP | OS | Connection | Status |
|--------|-------------|-----|------------|--------|
| Alex's MacBook Air | 100.98.1.21 | macOS | — | Active |
| iPad Pro 12.9 (Gen 3) | 100.97.182.16 | iOS | Relay (LAX) | Active |
| iPhone 15 Plus | 100.83.74.23 | iOS | — | Idle |
| Pi 5 (squishy-home) | 100.83.1.2 | Linux | Direct (192.168.0.189:41641) | Active |

**Observations:**
- ✅ Pi is using a **direct connection** (peer-to-peer over LAN) — fastest possible path
- ⚠️ iPad is going through a relay server in LAX — this means it's not on the same network, or NAT is preventing direction connection. Normal for mobile use.
- ✅ 4 devices total — manageable, all yours

### 4.2 Current Tailscale Security

| Check | Status | Notes |
|-------|--------|-------|
| Encryption | ✅ WireGuard (always on) | All traffic between devices is encrypted |
| No public ports | ✅ | Tailscale uses NAT traversal — no port forwarding needed |
| ACLs | ⚠️ **Not applied yet** | You have the policy file, but it's not in the admin console yet |
| MFA | ❓ Unknown | Check your identity provider settings |
| Key expiry | ❓ Unknown | Should be enabled to force periodic re-auth |
| Device approval | ❓ Unknown | Should require admin approval for new devices |

**Fix:** Apply the ACL policy (manual step from the previous session).

---

## 5. Smart Home Application Stack

### 5.1 What's Running

| Service | Host | Port | Auth | Encryption |
|---------|------|------|------|------------|
| Home Assistant | Pi (Docker) | 8123 | ✅ HA login + MFA | HTTP (not HTTPS) |
| Tool Broker | Pi (systemd) | 8000 | ✅ API key | HTTP |
| Ollama (local) | Pi (systemd) | 11434 | ❌ None | HTTP |
| Ollama (sidecar) | Mac | 11434 | ❌ None | HTTP |
| Dashboard | Pi (systemd) | 8050 | ❌ None | HTTP |
| Mosquitto MQTT | Pi (Docker) | 1883 | ✅ Username/password | Unencrypted |
| SonoBus | Pi (systemd) | 10998/UDP | ❌ None | Encrypted (built-in) |

### 5.2 Application-Level Security Controls

| Control | Status | Notes |
|---------|--------|-------|
| API key authentication | ✅ | Tool Broker requires `TOOL_BROKER_API_KEY` header |
| CORS allowlist | ⚠️ | Active but defaults don't match DEC-007 (DRIFT-08) |
| Rate limiting | ✅ | 60 req/60s on Tool Broker |
| PolicyGate (confirmation) | ✅ | Locks, alarms, garage doors require explicit confirmation |
| Entity validation | ✅ | LLM can't hallucinate devices — checked against HA registry |
| Tool whitelisting | ✅ | Only 5 pre-defined tools — no shell access |
| Audit logging | ✅ | All requests logged with request_id, IP, input/output |
| No credential exposure | ✅ | HA token from env var or Keychain, never in logs |

### 5.3 Known Vulnerabilities in Code

| # | Severity | Issue | Location | Status |
|---|----------|-------|----------|--------|
| 1 | **HIGH** | Shell injection via `shell=True` with user-controlled text | `jarvis/tts_controller.py:73` | ⬜ Not fixed |
| 2 | **HIGH** | Same shell injection pattern | `jarvis_audio/tts.py:104` | ⬜ Not fixed |
| 3 | **HIGH** | Placeholder returns fake transcription (not a security bug, but a correctness bug) | `secretary/core/transcription.py` | ⬜ Not fixed |
| 4 | **MEDIUM** | Calls nonexistent method `search_conversations()` | `memory/context_builder.py:174` | ⬜ Not fixed |
| 5 | **MEDIUM** | Vector store ID collisions — `hash(text) % 10000` / `% 100000` | `memory/vector_store.py:84,114,146` | ⬜ Not fixed |
| 6 | **MEDIUM** | CORS defaults contradict locked decision DEC-007 | `tool_broker/config.py:14` | ⬜ Not fixed |
| 7 | **MEDIUM** | `num_ctx` not passed to Ollama — potential memory pressure | `tool_broker/llm_client.py` | ⬜ Not fixed |
| 8 | **LOW** | Audit log grows unbounded (no rotation) | `tool_broker/audit_log.py` | ⬜ Not fixed |
| 9 | **LOW** | No `user_id` in audit log (needed for multi-user) | `tool_broker/audit_log.py` | ⬜ Not fixed |

---

## 6. Physical & Operational Security

These are things I can't check remotely, but you should think about:

### 6.1 Physical Access

| Question | Why It Matters |
|----------|----------------|
| Where is your Pi physically? | If someone can physically access it, they can pull the SD card / NVMe and read everything. FileVault is Mac-only. |
| Is your Mac in a locked room? | Disk is encrypted (FileVault), so stolen Mac is just hardware. But if it's unlocked and unattended, game over. |
| Who else has your WiFi password? | Everyone with it is on your network and can reach Pi services (until the firewall is applied). |

### 6.2 Backups

| Question | Status |
|----------|--------|
| HA backups configured? | ⬜ Not yet (P1-08 on roadmap) |
| Mac Time Machine? | ❓ Unknown |
| NVMe / SD card failure plan? | `bootstrap.sh` can rebuild from scratch, but HA config would be lost |

### 6.3 Password Hygiene

| Account | What to Check |
|---------|---------------|
| Router admin | Is it still the default? Change it. |
| HA admin | Strong password + MFA enabled? |
| Mac login | Strong password? Require password after sleep? |
| WiFi password | Strong, not shared widely? |
| Tailscale account | MFA enabled on your identity provider? |

---

## 7. Priority Action Plan (Ordered by Impact)

### Do Today (15 minutes)

| # | Action | Difficulty |
|---|--------|------------|
| 1 | **Turn on Mac firewall:** `sudo ./deploy/security/setup-firewall-mac.sh` | 1 command |
| 2 | **Apply Tailscale ACLs** (paste policy into admin console + tag devices) | 5 min in browser |
| 3 | **Check your router:** Log into http://192.168.0.1, disable UPnP, disable WPS, check port forwarding | 10 min |
| 4 | **Consider disabling Remote Login** if you don't use SSH to your Mac: System Settings → General → Sharing → Remote Login → OFF | 30 sec |

### Do This Week (1–2 hours)

| # | Action | Difficulty |
|---|--------|------------|
| 5 | **Run Pi firewall:** SSH to Pi, run `sudo ./deploy/security/setup-firewall-pi.sh` | 1 command |
| 6 | **Fix shell injection bugs** (#1, #2 above) — I can do this in your next coding session | Code change |
| 7 | **Fix CORS defaults** (DRIFT-08) — matches DEC-007 | Code change |
| 8 | **Update router firmware** | 5 min in router admin |
| 9 | **Enable WPA3** if your router supports it | Router WiFi settings |
| 10 | **Set Tailscale key expiry** in admin console | 2 min |

### Do This Month (ongoing)

| # | Action | Difficulty |
|---|--------|------------|
| 11 | **Set up HA backups** (P1-08 on roadmap) | 30 min |
| 12 | **Configure Time Machine** on Mac if not already | 10 min |
| 13 | **Change DNS** to NextDNS or Cloudflare (ad/malware blocking) | 5 min |
| 14 | **Add log rotation** for audit logs | Code change |
| 15 | **Create guest WiFi** network for visitors | Router admin |
| 16 | **Consider a better router** if your current one is ISP-provided | Research + purchase |

---

## 8. Concepts Explained (Since You're New to This)

### What is a firewall?
A firewall is a gatekeeper that decides which network traffic is allowed in and out. Think of your ports (8000, 8123, 11434) as doors in a building. Right now, **all the doors are open to anyone on your WiFi**. A firewall lets you say "only people with a badge (LAN + Tailscale IP) can enter door 8000."

### What is UPnP and why is it dangerous?
UPnP (Universal Plug and Play) lets devices on your network automatically tell your router "hey, open port 12345 to the internet and send traffic to me." This was designed for gaming and media streaming. The problem: malware on any device (smart TV, compromised IoT bulb, random laptop) can silently open a port that exposes your network to the internet. **Turn it off.**

### What is WPA2 vs WPA3?
Both encrypt your WiFi traffic. WPA2 has been around since 2004 and works fine. WPA3 (2018) fixes a weakness where an attacker who captures your WiFi handshake can try to brute-force your password offline. With WPA3, each device negotiates a unique key, so even if your password is weak, offline attacks don't work. If your router supports it, use WPA3.

### What is a VLAN?
A VLAN (Virtual LAN) is like having separate WiFi networks that can't see each other, even though they share the same hardware. You'd put your smart bulbs on VLAN 20 and your computers on VLAN 10. If a smart bulb gets hacked, it can't reach your Mac — it can only talk to Home Assistant (which you explicitly allow). Most consumer routers don't support VLANs; you'd need a prosumer router (ASUS Merlin, Ubiquiti, pfSense).

### Why does Ollama having no auth matter?
Ollama listens on port 11434 and accepts any request — no password, no API key, nothing. Anyone on your WiFi can `curl http://192.168.0.119:11434/api/generate -d '{"model":"qwen2.5:1.5b","prompt":"tell me secrets"}'` and get a response. It's not a huge risk because the LLM itself doesn't have access to your files or devices (that goes through the Tool Broker which DOES have auth). But it's unnecessary exposure. The firewall will restrict it to trusted sources.

### What is stealth mode?
When stealth mode is on, your Mac doesn't respond to network discovery probes (pings, port scans). An attacker scanning your network wouldn't even know your Mac exists. Right now it's off, so your Mac cheerfully responds "yes I'm here, and here are my open ports."

---

## 9. What I Cannot Check (Requires Your Action)

| Area | Why I Can't Check | What You Should Do |
|------|-------------------|-------------------|
| Router admin settings | Requires browser login with password | Log in at http://192.168.0.1 and verify the items in Section 3 |
| Pi firewall status | Pi is a separate device | SSH to Pi and run the firewall script |
| HA MFA status | Requires HA UI login | Check HA → Profile → MFA |
| iPhone/iPad security | Can't access iOS from Mac | Ensure devices have passcodes, biometrics, latest iOS |
| WiFi password strength | Not stored in a way I can read | You know it — is it long and random? |
| Router firmware version | Can't access router admin | Check in router admin UI |
| ISP modem/gateway | Separate from your router | If your ISP provides a modem+router combo, it may have its own UPnP, port forwarding, and remote management settings |

---

**END OF ASSESSMENT**

*Generated: 2026-03-05 by AI Agent (Claude Opus 4.6 via GitHub Copilot)*  
*Scope: MacBook Air M1 (macOS 26.1), Raspberry Pi 5 (Debian Bookworm), Tailscale mesh, local WiFi network*  
*Next review recommended: After applying firewall scripts and Tailscale ACLs*
