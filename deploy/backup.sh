#!/usr/bin/env bash
# =============================================================================
# Smart Home — Backup Script  (P1-08)
#
# Creates a timestamped backup of all critical Smart Home data:
#   1. Home Assistant config (Docker volume → ../ha_config)
#   2. AI Context (session artifacts, dossiers, memory)
#   3. Docker volume snapshots (Mosquitto, Pi-hole)
#   4. Deploy configs (systemd units, bootstrap)
#   5. Tool Broker audit logs
#
# Usage:
#   ./deploy/backup.sh                  # Full backup
#   ./deploy/backup.sh --config-only    # HA config only
#   BACKUP_DIR=/mnt/usb ./deploy/backup.sh  # Custom destination
#
# Restore:
#   tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz -C /target/dir
#
# Recommended: run daily via cron or systemd timer
#   crontab: 0 3 * * * /home/pi/Smart_Home/deploy/backup.sh >> /var/log/smart_home_backup.log 2>&1
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-${HOME}/smart_home_backups}"
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $(date +%H:%M:%S) $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $(date +%H:%M:%S) $*"; }
err()  { echo -e "${RED}[✗]${NC} $(date +%H:%M:%S) $*" >&2; }

# =============================================================================
# Parse args
# =============================================================================
CONFIG_ONLY=false
if [[ "${1:-}" == "--config-only" ]]; then
    CONFIG_ONLY=true
fi

# =============================================================================
# Setup
# =============================================================================
mkdir -p "${BACKUP_PATH}"
log "Starting Smart Home backup → ${BACKUP_PATH}"

# =============================================================================
# 1. Home Assistant config
# =============================================================================
HA_CONFIG="${REPO_DIR}/ha_config"
if [[ -d "$HA_CONFIG" ]]; then
    log "Backing up Home Assistant config..."
    # Exclude heavy directories that can be regenerated
    tar -czf "${BACKUP_PATH}/ha_config.tar.gz" \
        -C "$(dirname "$HA_CONFIG")" \
        --exclude='*.log' \
        --exclude='.storage/lovelace.resources' \
        --exclude='tts' \
        --exclude='deps' \
        "$(basename "$HA_CONFIG")" 2>/dev/null || warn "HA config backup had warnings (non-fatal)"
    log "  HA config: $(du -sh "${BACKUP_PATH}/ha_config.tar.gz" | cut -f1)"
else
    warn "HA config directory not found at ${HA_CONFIG} — skipping"
fi

if $CONFIG_ONLY; then
    log "Config-only mode — done."
    exit 0
fi

# =============================================================================
# 2. AI Context (lightweight — git-tracked, but includes session artifacts)
# =============================================================================
AI_CONTEXT="${REPO_DIR}/AI_CONTEXT"
if [[ -d "$AI_CONTEXT" ]]; then
    log "Backing up AI Context..."
    tar -czf "${BACKUP_PATH}/ai_context.tar.gz" \
        -C "$REPO_DIR" \
        "AI_CONTEXT" 2>/dev/null || warn "AI Context backup had warnings"
    log "  AI Context: $(du -sh "${BACKUP_PATH}/ai_context.tar.gz" | cut -f1)"
fi

# =============================================================================
# 3. Docker named volumes (Mosquitto data, Pi-hole config)
# =============================================================================
backup_docker_volume() {
    local volume_name="$1"
    local output_file="$2"
    if docker volume inspect "$volume_name" &>/dev/null; then
        log "Backing up Docker volume: ${volume_name}..."
        docker run --rm \
            -v "${volume_name}:/data:ro" \
            -v "${BACKUP_PATH}:/backup" \
            alpine tar -czf "/backup/${output_file}" -C /data . 2>/dev/null \
            || warn "Volume ${volume_name} backup had warnings"
        log "  ${volume_name}: $(du -sh "${BACKUP_PATH}/${output_file}" 2>/dev/null | cut -f1)"
    else
        warn "Docker volume ${volume_name} not found — skipping"
    fi
}

if command -v docker &>/dev/null; then
    backup_docker_volume "docker_mosquitto_data" "mosquitto_data.tar.gz"
    backup_docker_volume "docker_pihole_config"  "pihole_config.tar.gz"
    backup_docker_volume "docker_pihole_dnsmasq" "pihole_dnsmasq.tar.gz"
else
    warn "Docker not found — skipping volume backups"
fi

# =============================================================================
# 4. Deploy configs (systemd units, bootstrap, security scripts)
# =============================================================================
log "Backing up deploy configs..."
tar -czf "${BACKUP_PATH}/deploy.tar.gz" \
    -C "$REPO_DIR" \
    "deploy" 2>/dev/null || warn "Deploy backup had warnings"

# =============================================================================
# 5. Audit logs
# =============================================================================
AUDIT_DIR="${REPO_DIR}/tool_broker"
if ls "${AUDIT_DIR}"/audit_*.jsonl* &>/dev/null 2>&1; then
    log "Backing up audit logs..."
    tar -czf "${BACKUP_PATH}/audit_logs.tar.gz" \
        -C "$AUDIT_DIR" \
        $(cd "$AUDIT_DIR" && ls audit_*.jsonl* 2>/dev/null) 2>/dev/null \
        || warn "Audit log backup had warnings"
fi

# =============================================================================
# 6. Create combined archive
# =============================================================================
log "Creating combined archive..."
ARCHIVE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
tar -czf "$ARCHIVE" -C "$BACKUP_DIR" "$BACKUP_NAME" 2>/dev/null
rm -rf "$BACKUP_PATH"
log "Backup complete: ${ARCHIVE} ($(du -sh "$ARCHIVE" | cut -f1))"

# =============================================================================
# 7. Retention — clean up backups older than RETENTION_DAYS
# =============================================================================
if [[ -d "$BACKUP_DIR" ]]; then
    OLD_COUNT=$(find "$BACKUP_DIR" -name 'backup_*.tar.gz' -mtime +"$RETENTION_DAYS" | wc -l)
    if (( OLD_COUNT > 0 )); then
        log "Pruning ${OLD_COUNT} backup(s) older than ${RETENTION_DAYS} days..."
        find "$BACKUP_DIR" -name 'backup_*.tar.gz' -mtime +"$RETENTION_DAYS" -delete
    fi
fi

log "Done. Backup: ${ARCHIVE}"
