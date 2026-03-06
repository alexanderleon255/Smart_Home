# Session Handoff: Security Hardening (P4-02, P4-03)

**Date:** 2026-03-05  
**Session Focus:** Security Hardening — Tailscale ACLs + Local Firewall  
**Agent:** Claude Opus 4.6 via GitHub Copilot  
**Duration:** ~1 session  
**Roadmap Items:** P4-02, P4-03  

---

## What Was Done

### P4-02: Tailscale ACLs — ✅ COMPLETE (artifacts ready, manual apply pending)

**File:** `deploy/security/tailscale-acl-policy.jsonc`

Created a comprehensive Tailscale ACL policy with:
- **5 device tiers:** `tag:server` (Pi), `tag:sidecar` (Mac), `tag:mobile` (iPhone/iPad), `tag:admin` (future), `tag:guest` (no access)
- **2 user groups:** `group:admins` (Alex), `group:users` (future partner)
- **6 ACL rules:**
  1. Admin → all Pi/Mac ports (SSH, HA, broker, dashboard, Ollama, MQTT)
  2. Mobile → Pi user-facing only (HA, broker, dashboard)
  3. Pi → Mac Ollama (sidecar LLM tier routing)
  4. Mac → Pi broker/HA/Ollama (health checks, HA access)
  5. SonoBus audio (UDP 10998) for Jarvis voice: mobile ↔ server
  6. Users → HA + Dashboard only
- **SSH policy:** Restricted to `group:admins` only
- **10 built-in test assertions** that Tailscale auto-validates on save
- **Funnel denied** for all devices (no public exposure)

### P4-03: Local Firewall — ✅ COMPLETE (scripts ready, manual run pending)

**Files:**
- `deploy/security/setup-firewall-pi.sh` — UFW firewall for Pi 5
- `deploy/security/setup-firewall-mac.sh` — pf + App Firewall for Mac M1
- `deploy/security/verify-security.sh` — Security posture verification
- `deploy/security/README.md` — Full documentation with port inventory

**Pi Firewall (UFW) features:**
- Default deny incoming, allow outgoing
- 7 port rules: SSH (rate-limited), HA, Tool Broker, Dashboard, Ollama, MQTT (localhost+Docker+Tailscale only), SonoBus (UDP)
- Docker UFW compatibility (DOCKER-USER chain in after.rules)
- Allowed sources: LAN (192.168.0.0/16) + Tailscale (100.64.0.0/10) + Docker (172.16.0.0/12)

**Mac Firewall (pf) features:**
- macOS Application Firewall enabled with stealth mode
- pf rules: allow Ollama (11434) from trusted networks only
- Tailscale utun interfaces allowed (Tailscale handles its own ACLs)
- Anchor-based integration with /etc/pf.conf
- Backup created before modifying system config

**Verification script features:**
- Tailscale status + connectivity checks
- Port reachability tests (both Pi and Mac services)
- UFW status checks (Pi-specific)
- pf/App Firewall checks (Mac-specific)
- Best-practice checks (API key, HA token, hardcoded passwords)
- Colored output with PASS/FAIL/WARN summary

### Supporting Changes

- `deploy/bootstrap.sh` — Added Step 10 (firewall setup, interactive prompt)
- Updated "Next steps" to include ACL application and security verification

---

## What Was NOT Done (Manual Steps Required)

These require human action — cannot be automated via code:

1. **Apply Tailscale ACLs:** Paste `tailscale-acl-policy.jsonc` into https://login.tailscale.com/admin/acls
2. **Assign device tags:** In Tailscale admin → Machines:
   - Pi 5 → `tag:server`
   - Mac M1 → `tag:sidecar`
   - iPhone → `tag:mobile`
   - iPad → `tag:mobile`
3. **Run Pi firewall:** SSH to Pi, then `sudo ./deploy/security/setup-firewall-pi.sh`
4. **Run Mac firewall:** `sudo ./deploy/security/setup-firewall-mac.sh`
5. **Verify both:** Run `./deploy/security/verify-security.sh` from any tailnet device
6. **Port scan:** Run `nmap -sV 100.83.1.2` from a non-admin device to confirm restricted access

---

## Test Results

- **248 tests passing** (unchanged — security changes are infrastructure-only, no Python code modified)
- **18.47s** test runtime

---

## Updated Metrics

| Metric | Before | After |
|--------|--------|-------|
| Items complete | 37/62 (60%) | 39/62 (63%) |
| P4 Security | 2/6 (33%) | 4/6 (67%) |
| Tests | 248 | 248 |
| New files | — | 5 (4 scripts + 1 README) |

---

## Remaining P4 Items

| Item | Status | Notes |
|------|--------|-------|
| P4-05 | ⬜ NOT STARTED | Logging & Monitoring (HA full logging, 30-day retention, alerts) |
| P4-06 | ⬜ NOT STARTED | Security Audit (nmap scan, ACL verification, TTS shell injection fix) |

**Note:** P4-06 depends on P4-02/P4-03 being applied (manual steps above), and the shell injection fix (Bug #1, #2) from Tier 1 bugs should be done first.

---

## Next Recommended Actions (Priority Order)

1. **Apply the manual steps** listed above (ACLs + firewall scripts)
2. **Fix Tier 1 bugs** — Shell injection in tts_controller.py and tts.py (HIGH priority, security-related)
3. **DRIFT-08 (CORS fix)** — Code contradicts locked DEC-007; quick fix in config.py
4. **P6-07 Jarvis Modelfile** — Quick win (1h), mostly exists as template already
5. **P4-05 Logging & Monitoring** — Log rotation for audit log, HA logging

---

## Files Modified/Created

| File | Action |
|------|--------|
| `deploy/security/tailscale-acl-policy.jsonc` | **Created** — Tailscale ACL policy |
| `deploy/security/setup-firewall-pi.sh` | **Created** — Pi UFW setup script |
| `deploy/security/setup-firewall-mac.sh` | **Created** — Mac pf setup script |
| `deploy/security/verify-security.sh` | **Created** — Security verification script |
| `deploy/security/README.md` | **Created** — Security documentation |
| `deploy/bootstrap.sh` | **Modified** — Added firewall step + updated next steps |
| `AI_CONTEXT/.../2026-03-05_smart_home_master_roadmap.md` | **Modified** — P4-02, P4-03 → COMPLETE |
| `AI_CONTEXT/.../smart_home_progress_tracker.md` | **Modified** — P4 67%, session log entry |

---

**END OF HANDOFF**
