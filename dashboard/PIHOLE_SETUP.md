# Pi-hole Integration Guide

## Current Status

**✓ Complete:**
- Docker Compose deployment (`docker/docker-compose.yml`)
- Web UI accessible at `http://<pi-ip>:8080/admin/`
- Admin password: `pihole_admin_2026` (set in docker-compose.yml)
- Dashboard shows Pi-hole connectivity status

**⏳ Pending:**
- Full API v6 endpoint integration for live statistics (queries, blocks, blocklist size)
- Automatic printer/IoT device blocking detection
- Once API endpoints are confirmed, uncomment the functions and tests in `dashboard/app.py` (search for TODO comments)

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
PIHOLE_ADMIN_PASSWORD=pihole_admin_2026
```

### 3. Test connectivity

```bash
# From Mac:
curl -s http://100.83.1.2:8080/admin/ | head -20
# Should return HTML with "Pi-hole" in the title
```

---

## Dashboard Panel Behavior

**When Pi-hole is reachable:**
- Status badge shows **ENABLED** (green)
- Explanatory note: "Web UI accessible. API queries pending."
- Admin link provided to open web dashboard

**When Pi-hole is unreachable:**
- Status badge shows disconnected (red)
- Message: "Check that Docker container is running"
- Helpful troubleshooting command provided

---

## Blocking Devices / Whitelist Management

### Current Approach (manual)

1. Open `http://100.83.1.2:8080/admin/` in browser
2. Login with password: `pihole_admin_2026`
3. Go to **Adlist** → **Whitelist** to allow specific domains
4. For printer or specific devices, whitelist their manufacturer domains:
   - HP: `hp.com`, `hplipoutlet.com`
   - Example: your printer tries to reach `update.hp.com` → add to whitelist

### Future Approach (pending API integration)

Once Pi-hole v6 API is integrated:
- Dashboard will automatically detect blocked printer/device domains
- Alert badge in dashboard with specific domains to whitelist
- Suggested actions to resolve

---

## Pi-hole v6 API Discovery

The v6 API structure differs from v5. When confirmed, endpoints will be similar to:

```bash
# Example (to be verified):
curl -s "http://pi.hole:8080/api/dns/..."  # New structure
```

To help discover the correct endpoints, check the Pi-hole logs:

```bash
docker exec pihole **tail -20** /var/log/pihole/pihole.log**
```

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
3. Update in `.env` or code references

---

## References

- Pi-hole Official Docs: https://docs.pi-hole.net/
- Docker Hub Image: `pihole/pihole:latest`
- Roadmap: See `AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/` for related tasks
