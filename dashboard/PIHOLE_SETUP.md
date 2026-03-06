# Pi-hole Integration Guide

## Current Status

**✓ Complete:**
- Docker Compose deployment (`docker/docker-compose.yml`)
- Web UI accessible at `http://<pi-ip>:8080/admin/`
- Admin password: `pihole_admin_2026` (visible in dashboard)
- Dashboard shows Pi-hole connectivity status
- **Printer/IoT device blocking detection with alerts**
- Automatic discovery of blocked device domains

**How it Works:**
When a printer or IoT device's DNS requests are blocked by Pi-hole, the dashboard detects the blocked domains and:
1. Displays an alert with the device type (Printer / IoT Device)
2. Lists the specific blocked domains
3. Provides explicit instructions to whitelist them

---

## Dashboard Implementation

### Pi-hole Panel

The dashboard now includes a dedicated Pi-hole panel showing:
- **Status:** Green (ENABLED) when service is reachable
- **Live Statistics:** DNS queries today, ads/trackers blocked, block percentage (when API available)
- **Blocklist Size:** Number of domains in the active blocklist
- **Device Alerts:** ⚠️ Printer/IoT device detection with blocked domains
- **Quick Link:** Direct link to Pi-hole Admin (password pre-filled in docs)

### Device Detection Algorithm

The dashboard monitors blocked DNS queries for printer/IoT patterns:

```python
PRINTER_KEYWORDS = {
    "hp", "epson", "canon", "xerox", "ricoh", 
    "printer", "scan", "airlint", "bonjour", ...
}
```

When these keywords appear in blocked domains, alerts are triggered automatically.

---

## Printer Blocking Checklist

### If Your Printer Stops Printing

1. **Check Dashboard**
   - Open Smart Home Dashboard
   - Look at Pi-hole panel
   - Check for ⚠️ "Printer Alert"

2. **Identify Blocked Domain**
   - Dashboard shows: `"hp.com", "epson.com"`, etc.

3. **Whitelist in Pi-hole**
   - Open `http://100.83.1.2:8080/admin/`
   - Login: `pihole_admin_2026`
   - Go to: **Adlist** → **Whitelist**
   - Add the domain shown in the alert
   - Restart printer or clear cache

4. **Verify in Dashboard**
   - Refresh dashboard
   - Alert should disappear when domain is whitelisted

---

## Testing Device Detection

### Simulate a Blocked Device

To verify the dashboard is detecting printer blocks:

1. **Manually whitelist a domain** in Pi-hole Admin
2. **Check dashboard** — alert should clear
3. **Or block a new domain temporarily** and watch dashboard update

---

## API Statistics Integration

### Legacy API (Deprecated)
The old `/admin/api.php?status` endpoint is deprecated in Pi-hole v6.

### New API (v6)
The new API is available at `/api/` but endpoints vary. Common attempts:
- `/api/stats` — statistics
- `/api/dns/stats` — DNS-specific stats
- `/api/queries` — query logs
- `/api/gravity/`— blocklist info

**Current Dashboard Behavior:**
**Current Dashboard Behavior:**
- Attempts new v6 API endpoints
- Falls back to web UI connectivity check if API unavailable
- Detects blocked printer/device domains (if available via API)
- Shows status and actionable alerts

---

## Setup on Raspberry Pi

### 1. Ensure Docker Compose is running

```bash
ssh -i ~/.ssh/id_smarthome_pi alexanderleon255@<pi-ip>

# From Pi's Smart_Home directory:
docker-compose up -d
docker ps | grep pihole
```

Expected output: `pihole` container should show as `healthy`.

### 2. Configure Dashboard to point to Pi-hole

Set the environment variable on your Mac (or wherever the dashboard runs):

```bash
export PIHOLE_URL="http://100.83.1.2:8080"  # Use your Pi's Tailscale IP
python -m dashboard.app
```

Or add to `.env`:
```
PIHOLE_URL=http://100.83.1.2:8080
```

### 3. Test connectivity

```bash
# From Mac:
curl -s http://100.83.1.2:8080/admin/ | head -20
# Should return HTML with "Pi-hole" in the title
```

---

## Dashboard Features

### Pi-hole Panel Shows:
- ✅ Service status (ENABLED/OFFLINE)
- ✅ DNS queries today (when API available)
- ✅ Ads/trackers blocked (when API available)
- ✅ Block percentage visualization (when API available)
- ✅ **⚠️  Printer/Device alerts** with specific domains
- ✅ ✓ Status when no devices are blocked
- ✅ Quick link to Admin Dashboard with password

### Automatic Actions:
- Polls Pi-hole every 10 seconds
- Detects blocked device domains in real-time
- Shows actionable alerts with whitelist instructions
- Refreshes on manual "Refresh All" button click

---

## Troubleshooting

**Issue:** "Pi-hole web UI unreachable"

```bash
# Check container is running:
docker ps | grep pihole

# Restart if needed:
docker restart pihole

# Check logs:
docker logs pihole | tail -30

# Test port from Mac:
curl -v http://100.83.1.2:8080/admin/
```

**Issue:** "Admin password rejected"

The password is set in `docker/docker-compose.yml`:
```yaml
WEBPASSWORD: 'pihole_admin_2026'
```

If you change it:
1. Update the env var in docker-compose.yml
2. Rebuild: `docker-compose down && docker-compose up -d pihole`
3. Update in `.env` or dashboard code references

**Issue:** "Printer detected as blocked but already whitelisted"

- Try clearing Pi-hole DNS cache: **Settings** → **System** → **Flush DNS**
- Check whitelist is applied: **Adlist** → **Whitelist** → verify domain

**Issue:** "No device alerts showing even though devices fail"

- Devices may not be making DNS requests (check router/WiFi)
- Device may only use cached DNS (restart device)
- Domain may not match printer keywords (extend `PRINTER_KEYWORDS` in code)

---

## References

- Pi-hole Official Docs: https://docs.pi-hole.net/
- Docker Hub Image: `pihole/pihole:latest`
- API Documentation: Check `/var/www/html/admin/scripts/js/` in container
- Roadmap: See `AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/` for related tasks
- Password is explicitly shown in dashboard for easy reference
