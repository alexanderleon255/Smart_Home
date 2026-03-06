#!/usr/bin/env bash
# =============================================================================
# Smart Home — Pi 5 Bootstrap Script
#
# Deploys the entire Smart Home stack from a fresh Raspberry Pi OS (Bookworm).
# Run as the target user (NOT root):
#
#   git clone https://github.com/alexanderleon255/Smart_Home.git ~/Smart_Home
#   cd ~/Smart_Home && ./deploy/bootstrap.sh
#
# What this script does:
#   1. Installs system packages (Docker, PipeWire, build tools)
#   2. Installs Ollama
#   3. Creates Python virtualenv + installs requirements
#   4. Installs (symlinks) systemd user units from deploy/systemd/
#   5. Enables linger (services start at boot, no login required)
#   6. Starts Docker containers (Home Assistant + Mosquitto)
#   7. Pulls the default LLM model
#   8. Enables and starts all services
#
# Prerequisites:
#   - Raspberry Pi 5, Raspberry Pi OS Bookworm (64-bit)
#   - Internet connectivity
#   - User has sudo access
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
VENV_DIR="${REPO_DIR}/.venv"
DEFAULT_MODEL="qwen2.5:1.5b"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }

# =============================================================================
# 1. System packages
# =============================================================================
install_system_packages() {
    log "Installing system packages…"
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        docker.io docker-compose-plugin \
        pipewire pipewire-pulse pipewire-jack \
        python3 python3-venv python3-pip \
        build-essential git curl wget \
        portaudio19-dev libsndfile1 \
        pulseaudio-utils \
        jq

    # Ensure current user is in docker group
    if ! groups | grep -q docker; then
        sudo usermod -aG docker "$USER"
        warn "Added $USER to docker group — you may need to log out/in for Docker to work without sudo"
    fi

    # Enable Docker at boot
    sudo systemctl enable docker
    sudo systemctl start docker || true

    log "System packages installed"
}

# =============================================================================
# 2. Ollama
# =============================================================================
install_ollama() {
    if command -v ollama &>/dev/null; then
        log "Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown version')"
        return
    fi
    log "Installing Ollama…"
    curl -fsSL https://ollama.com/install.sh | sh
    log "Ollama installed"
}

# =============================================================================
# 3. Python virtualenv
# =============================================================================
setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log "Creating Python virtualenv…"
        python3 -m venv "$VENV_DIR"
    fi
    log "Installing Python dependencies…"
    "$VENV_DIR/bin/pip" install -q --upgrade pip
    "$VENV_DIR/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
    log "Python environment ready"
}

# =============================================================================
# 4. Systemd user units (symlink from repo)
# =============================================================================
install_systemd_units() {
    log "Installing systemd user units…"
    mkdir -p "$SYSTEMD_USER_DIR"

    for unit_file in "$SCRIPT_DIR/systemd/"*.service; do
        unit_name="$(basename "$unit_file")"
        target="$SYSTEMD_USER_DIR/$unit_name"

        # Remove existing (file or symlink) and replace with symlink
        if [[ -e "$target" ]] || [[ -L "$target" ]]; then
            rm "$target"
        fi
        ln -s "$unit_file" "$target"
        log "  Linked $unit_name"
    done

    systemctl --user daemon-reload
    log "Systemd units installed and daemon reloaded"
}

# =============================================================================
# 5. Linger (services survive logout)
# =============================================================================
enable_linger() {
    if loginctl show-user "$USER" 2>/dev/null | grep -q "Linger=yes"; then
        log "Linger already enabled"
        return
    fi
    log "Enabling linger for $USER…"
    sudo loginctl enable-linger "$USER"
    log "Linger enabled"
}

# =============================================================================
# 6. Docker containers (Home Assistant + Mosquitto)
# =============================================================================
start_docker_services() {
    log "Starting Docker containers…"
    # Create ha_config dir if missing (first run)
    mkdir -p "$REPO_DIR/ha_config"

    if command -v docker &>/dev/null; then
        (cd "$REPO_DIR/docker" && docker compose up -d)
        log "Docker containers started"
    else
        warn "Docker not yet available (may need re-login for group membership)"
    fi
}

# =============================================================================
# 7. Pull default LLM model
# =============================================================================
pull_model() {
    log "Pulling default LLM model ($DEFAULT_MODEL)…"
    # Start ollama temporarily if not already running
    local need_stop=false
    if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
        OLLAMA_HOST=0.0.0.0 ollama serve &>/dev/null &
        local ollama_pid=$!
        need_stop=true
        sleep 3
    fi

    ollama pull "$DEFAULT_MODEL"

    if $need_stop; then
        kill "$ollama_pid" 2>/dev/null || true
        wait "$ollama_pid" 2>/dev/null || true
    fi
    log "Model $DEFAULT_MODEL ready"
}

# =============================================================================
# 8. Enable and start services
# =============================================================================
enable_services() {
    log "Enabling and starting services…"

    local services=(
        ollama.service
        tool-broker.service
        dashboard.service
        jarvis-audio-devices.service
        sonobus.service
    )

    for svc in "${services[@]}"; do
        systemctl --user enable "$svc" 2>/dev/null || warn "Could not enable $svc"
        systemctl --user start "$svc" 2>/dev/null || warn "Could not start $svc"
        log "  $svc enabled + started"
    done
}

# =============================================================================
# 9. Tailscale (optional — prompt user)
# =============================================================================
install_tailscale() {
    if command -v tailscale &>/dev/null; then
        log "Tailscale already installed"
        return
    fi
    echo ""
    read -rp "Install Tailscale for secure mesh VPN? [Y/n] " yn
    yn="${yn:-Y}"
    if [[ "$yn" =~ ^[Yy] ]]; then
        curl -fsSL https://tailscale.com/install.sh | sh
        warn "Run 'sudo tailscale up' to authenticate after installation"
    else
        warn "Skipping Tailscale — sidecar LLM tier will not be available"
    fi
}

# =============================================================================
# 10. Firewall (UFW) — optional but recommended
# =============================================================================
setup_firewall() {
    local fw_script="$SCRIPT_DIR/security/setup-firewall-pi.sh"
    if [[ ! -f "$fw_script" ]]; then
        warn "Firewall script not found at $fw_script — skipping"
        return
    fi
    echo ""
    read -rp "Set up UFW firewall? (recommended for security) [Y/n] " yn
    yn="${yn:-Y}"
    if [[ "$yn" =~ ^[Yy] ]]; then
        sudo bash "$fw_script"
    else
        warn "Skipping firewall — run 'sudo deploy/security/setup-firewall-pi.sh' later"
    fi
}

# =============================================================================
# Verification
# =============================================================================
verify() {
    echo ""
    log "=== Verification ==="

    # Ollama
    if systemctl --user is-active -q ollama.service; then
        log "Ollama: active"
    else
        warn "Ollama: not active"
    fi

    # Tool Broker
    if systemctl --user is-active -q tool-broker.service; then
        log "Tool Broker: active"
        sleep 2
        if curl -sf http://localhost:8000/v1/health | jq -r '.status' 2>/dev/null; then
            :
        else
            warn "Tool Broker health check failed (may still be starting)"
        fi
    else
        warn "Tool Broker: not active"
    fi

    # Dashboard
    if systemctl --user is-active -q dashboard.service; then
        log "Dashboard: active"
    else
        warn "Dashboard: not active"
    fi

    # Docker
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q homeassistant; then
        log "Home Assistant: running"
    else
        warn "Home Assistant: not running"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q mosquitto; then
        log "Mosquitto: running"
    else
        warn "Mosquitto: not running"
    fi

    echo ""
    log "Bootstrap complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Home Assistant at http://$(hostname -I | awk '{print $1}'):8123"
    echo "  2. Set HA_TOKEN in $REPO_DIR/.env or environment"
    echo "  3. If using sidecar LLM: set SIDECAR_OLLAMA_URL in environment"
    echo "  4. View dashboard at http://localhost:8050"
    echo "  5. Apply Tailscale ACLs: see deploy/security/README.md"
    echo "  6. Verify security: ./deploy/security/verify-security.sh"
    echo ""
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "========================================"
    echo "  Smart Home — Pi 5 Bootstrap"
    echo "========================================"
    echo "Repo:   $REPO_DIR"
    echo "User:   $USER"
    echo "Arch:   $(uname -m)"
    echo ""

    install_system_packages
    install_ollama
    setup_venv
    install_systemd_units
    enable_linger
    start_docker_services
    pull_model
    enable_services
    install_tailscale
    setup_firewall
    verify
}

main "$@"
