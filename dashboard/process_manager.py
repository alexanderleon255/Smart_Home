"""
Process Manager — starts/stops/monitors Ollama and Tool Broker.

Uses synchronous httpx for health checks (called from Dash callbacks)
and subprocess.Popen for launching services.
"""

import logging
import os
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class ServiceState:
    name: str
    status: ServiceStatus = ServiceStatus.STOPPED
    pid: Optional[int] = None
    url: Optional[str] = None
    model: Optional[str] = None
    detail: Optional[str] = None
    last_check: float = 0.0


class ProcessManager:
    """Manages Tool Broker and Ollama processes."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        broker_url: str = "http://localhost:8000",
        broker_host: str = "127.0.0.1",
        broker_port: int = 8000,
        ollama_model: str = "llama3.1:8b",
    ):
        self.ollama_url = ollama_url
        self.broker_url = broker_url
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.ollama_model = ollama_model

        self.ollama = ServiceState(name="Ollama", url=ollama_url)
        self.broker = ServiceState(name="Tool Broker", url=broker_url)

        self._broker_proc: Optional[subprocess.Popen] = None
        self._ollama_proc: Optional[subprocess.Popen] = None
        self._broker_log_lines: list[str] = []

    # ------------------------------------------------------------------
    # Health checks  (synchronous — safe for Dash callbacks)
    # ------------------------------------------------------------------

    def check_ollama(self) -> ServiceState:
        """Ping Ollama /api/tags."""
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=4.0)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                base = self.ollama_model.split(":")[0]
                has_model = any(base in m for m in models)
                self.ollama.status = ServiceStatus.RUNNING
                if has_model:
                    self.ollama.model = self.ollama_model
                    self.ollama.detail = f"{len(models)} model(s) available"
                else:
                    self.ollama.model = None
                    self.ollama.detail = (
                        f"Running but '{self.ollama_model}' not found. "
                        f"Run: ollama pull {self.ollama_model}"
                    )
            else:
                self.ollama.status = ServiceStatus.ERROR
                self.ollama.detail = f"HTTP {resp.status_code}"
        except httpx.ConnectError:
            self.ollama.status = ServiceStatus.STOPPED
            self.ollama.detail = "Not running"
        except Exception as exc:
            self.ollama.status = ServiceStatus.ERROR
            self.ollama.detail = str(exc)[:120]
        self.ollama.last_check = time.time()
        return self.ollama

    def check_broker(self) -> ServiceState:
        """Ping Tool Broker /v1/health."""
        if self._broker_proc and self._broker_proc.poll() is not None:
            self._broker_proc = None

        try:
            resp = httpx.get(f"{self.broker_url}/v1/health", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                self.broker.status = ServiceStatus.RUNNING
                self.broker.model = data.get("model")
                ha = "HA connected" if data.get("ha_connected") else "HA disconnected"
                entities = data.get("entity_cache_size", 0)
                self.broker.detail = f"{ha} · {entities} entities cached"
            else:
                self.broker.status = ServiceStatus.ERROR
                self.broker.detail = f"HTTP {resp.status_code}"
        except httpx.ConnectError:
            self.broker.status = ServiceStatus.STOPPED
            self.broker.detail = "Not running"
        except Exception as exc:
            self.broker.status = ServiceStatus.ERROR
            self.broker.detail = str(exc)[:120]
        self.broker.last_check = time.time()
        return self.broker

    def check_all(self):
        """Run all health checks."""
        self.check_ollama()
        self.check_broker()

    # ------------------------------------------------------------------
    # Ollama management
    # ------------------------------------------------------------------

    def start_ollama(self) -> str:
        """Start Ollama serve in background."""
        self.check_ollama()
        if self.ollama.status == ServiceStatus.RUNNING:
            return "Ollama is already running."
        try:
            self._ollama_proc = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.ollama.status = ServiceStatus.STARTING
            self.ollama.pid = self._ollama_proc.pid
            time.sleep(2)
            self.check_ollama()
            if self.ollama.status == ServiceStatus.RUNNING:
                return f"Ollama started (PID {self._ollama_proc.pid})"
            return f"Ollama starting (PID {self._ollama_proc.pid})…"
        except FileNotFoundError:
            self.ollama.status = ServiceStatus.ERROR
            self.ollama.detail = "ollama not found"
            return "Error: ollama binary not found. Install from https://ollama.com"
        except Exception as exc:
            self.ollama.status = ServiceStatus.ERROR
            self.ollama.detail = str(exc)[:120]
            return f"Error: {exc}"

    def stop_ollama(self) -> str:
        """Stop Ollama (kills the serve process)."""
        self.check_ollama()
        if self.ollama.status != ServiceStatus.RUNNING:
            return "Ollama is not running."
        try:
            # If we spawned it, kill our child
            if self._ollama_proc and self._ollama_proc.poll() is None:
                self._ollama_proc.terminate()
                try:
                    self._ollama_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._ollama_proc.kill()
                self._ollama_proc = None
                self.ollama.status = ServiceStatus.STOPPED
                self.ollama.pid = None
                self.ollama.detail = "Stopped"
                return "Ollama stopped."
            # Otherwise try pkill (e.g. if started externally)
            subprocess.run(
                ["pkill", "-f", "ollama serve"],
                capture_output=True, timeout=5,
            )
            time.sleep(1)
            self.check_ollama()
            if self.ollama.status == ServiceStatus.STOPPED:
                return "Ollama stopped."
            return "Stop signal sent, but Ollama is still responding."
        except Exception as exc:
            return f"Error stopping Ollama: {exc}"

    # ------------------------------------------------------------------
    # Tool Broker management
    # ------------------------------------------------------------------

    def start_broker(self) -> str:
        """Start Tool Broker as subprocess."""
        self.check_broker()
        if self.broker.status == ServiceStatus.RUNNING:
            return "Tool Broker is already running."

        if self._broker_proc and self._broker_proc.poll() is None:
            return "Tool Broker subprocess already active, waiting…"

        smart_home_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["HOST"] = self.broker_host
        env["PORT"] = str(self.broker_port)

        try:
            self._broker_log_lines = []
            self._broker_proc = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn",
                    "tool_broker.main:app",
                    "--host", self.broker_host,
                    "--port", str(self.broker_port),
                ],
                cwd=smart_home_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.broker.pid = self._broker_proc.pid
            self.broker.status = ServiceStatus.STARTING

            time.sleep(3)
            self._drain_broker_output()
            self.check_broker()

            if self.broker.status == ServiceStatus.RUNNING:
                return f"Tool Broker started (PID {self._broker_proc.pid})"

            if self._broker_proc.poll() is not None:
                recent = "\n".join(self._broker_log_lines[-5:])
                self.broker.status = ServiceStatus.ERROR
                self.broker.detail = f"Exited with code {self._broker_proc.returncode}"
                return f"Tool Broker crashed:\n{recent}"

            return f"Tool Broker starting (PID {self._broker_proc.pid})…"
        except Exception as exc:
            self.broker.status = ServiceStatus.ERROR
            self.broker.detail = str(exc)[:120]
            return f"Error: {exc}"

    def stop_broker(self) -> str:
        """Stop Tool Broker subprocess."""
        if self._broker_proc and self._broker_proc.poll() is None:
            self._broker_proc.terminate()
            try:
                self._broker_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._broker_proc.kill()
            self._broker_proc = None
            self.broker.status = ServiceStatus.STOPPED
            self.broker.pid = None
            self.broker.detail = "Stopped"
            return "Tool Broker stopped."
        self.broker.status = ServiceStatus.STOPPED
        return "Tool Broker was not running."

    def _drain_broker_output(self) -> None:
        """Non-blocking read of broker stdout."""
        if not self._broker_proc or not self._broker_proc.stdout:
            return
        while select.select([self._broker_proc.stdout], [], [], 0)[0]:
            line = self._broker_proc.stdout.readline()
            if not line:
                break
            self._broker_log_lines.append(line.rstrip())
            if len(self._broker_log_lines) > 200:
                self._broker_log_lines = self._broker_log_lines[-100:]

    def get_broker_logs(self) -> list[str]:
        """Get recent broker log lines."""
        self._drain_broker_output()
        return list(self._broker_log_lines[-100:])

    # ------------------------------------------------------------------
    # Tailscale / Network checks
    # ------------------------------------------------------------------

    def check_tailscale(self) -> dict:
        """Check Tailscale status and peer list.

        Returns dict with keys: installed, running, ip, peers (list of dicts),
        rpi (dict or None for the Raspberry Pi peer).
        """
        result = {
            "installed": False,
            "running": False,
            "ip": None,
            "peers": [],
            "rpi": None,
            "detail": "Not installed",
        }
        # Find the tailscale binary — macOS app or Homebrew CLI
        ts_bin = None
        for candidate in [
            "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
            "/usr/local/bin/tailscale",
            "/opt/homebrew/bin/tailscale",
        ]:
            if os.path.isfile(candidate):
                ts_bin = candidate
                break
        if ts_bin is None:
            # Fall back to PATH
            which = subprocess.run(
                ["which", "tailscale"], capture_output=True, text=True, timeout=3,
            )
            if which.returncode == 0 and which.stdout.strip():
                ts_bin = which.stdout.strip()
        if ts_bin is None:
            return result

        result["installed"] = True
        try:

            status = subprocess.run(
                [ts_bin, "status", "--json"],
                capture_output=True, text=True, timeout=5,
            )
            if status.returncode != 0:
                result["detail"] = "Installed but not running"
                return result

            import json as _json
            data = _json.loads(status.stdout)
            result["running"] = True

            # Self info
            self_node = data.get("Self", {})
            ts_ips = self_node.get("TailscaleIPs", [])
            result["ip"] = ts_ips[0] if ts_ips else None

            # Parse peers
            peer_map = data.get("Peer", {})
            for _key, peer in peer_map.items():
                # Prefer DNSName (e.g. "iphone-15-plus"), fall back to HostName
                dns = peer.get("DNSName", "")
                # DNSName often ends with ".tail12345.ts.net." — strip the domain
                if dns:
                    name = dns.split(".")[0]
                else:
                    name = peer.get("HostName", "unknown")
                online = peer.get("Online", False)
                peer_ips = peer.get("TailscaleIPs", [])
                os_name = peer.get("OS", "")
                entry = {
                    "name": name,
                    "ip": peer_ips[0] if peer_ips else None,
                    "online": online,
                    "os": os_name,
                }
                result["peers"].append(entry)
                # Detect RPI (common indicators)
                lower_name = name.lower()
                if any(tag in lower_name for tag in ("rpi", "raspberry", "pi5", "pi4", "homeassistant", "ha-")):
                    result["rpi"] = entry

            online_count = sum(1 for p in result["peers"] if p["online"])
            result["detail"] = f"{online_count}/{len(result['peers'])} peers online"

        except FileNotFoundError:
            result["detail"] = "tailscale binary not found"
        except subprocess.TimeoutExpired:
            result["detail"] = "Tailscale status timed out"
        except Exception as exc:
            result["detail"] = str(exc)[:100]
        return result

    # ------------------------------------------------------------------
    # Voice / Secretary checks
    # ------------------------------------------------------------------

    def check_voice_services(self) -> dict:
        """Check if Jarvis voice loop or Secretary engine processes are running.

        First checks the voice status file (written by VoiceServiceManager),
        then falls back to ps aux scanning.

        Returns dict: voice_loop (bool), secretary (bool), whisper (bool),
                      detail, voice_status (rich status from status file or None).
        """
        result = {
            "voice_loop": False,
            "secretary": False,
            "whisper": False,
            "detail": "No voice services detected",
            "voice_status": None,
        }

        # Check voice status file first (rich data from VoiceServiceManager)
        try:
            from jarvis.service import VoiceServiceManager
            vs = VoiceServiceManager.read_status()
            if vs and vs.get("alive"):
                result["voice_loop"] = True
                result["voice_status"] = vs
        except Exception:
            pass

        # Fall back / supplement with ps aux
        try:
            ps = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5,
            )
            lines = ps.stdout.lower()
            if not result["voice_loop"] and ("voice_loop" in lines or "jarvis" in lines):
                result["voice_loop"] = True
            if "secretary" in lines:
                result["secretary"] = True
            if "whisper" in lines:
                result["whisper"] = True

            active = []
            if result["voice_loop"]:
                active.append("Voice Loop")
            if result["secretary"]:
                active.append("Secretary")
            if result["whisper"]:
                active.append("Whisper STT")
            result["detail"] = ", ".join(active) + " active" if active else "No voice services detected"
        except Exception as exc:
            result["detail"] = str(exc)[:100]
        return result

    def start_voice(self) -> str:
        """Start Jarvis voice loop as a background subprocess."""
        vs = self.check_voice_services()
        if vs["voice_loop"]:
            return "Voice loop is already running."

        smart_home_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            self._voice_proc = subprocess.Popen(
                [sys.executable, "-m", "jarvis"],
                cwd=smart_home_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)
            return f"Jarvis voice loop started (PID {self._voice_proc.pid})"
        except Exception as exc:
            return f"Error starting voice loop: {exc}"

    def stop_voice(self) -> str:
        """Stop Jarvis voice loop."""
        # Try our subprocess first
        if hasattr(self, "_voice_proc") and self._voice_proc and self._voice_proc.poll() is None:
            self._voice_proc.terminate()
            try:
                self._voice_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._voice_proc.kill()
            self._voice_proc = None
            return "Voice loop stopped."

        # Try killing by PID from status file
        try:
            from jarvis.service import VoiceServiceManager
            vs = VoiceServiceManager.read_status()
            if vs and vs.get("pid") and vs.get("alive"):
                import signal
                os.kill(vs["pid"], signal.SIGTERM)
                time.sleep(1)
                return f"Voice loop (PID {vs['pid']}) stopped."
        except Exception:
            pass

        return "Voice loop was not running."

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def shutdown(self):
        """Clean up subprocesses."""
        self.stop_broker()