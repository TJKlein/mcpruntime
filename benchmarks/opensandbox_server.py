"""Ensure OpenSandbox server is running so the benchmark can evaluate the opensandbox backend."""

import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN = "localhost:8080"
DEFAULT_CONFIG = os.path.expanduser("~/.sandbox.toml")
READY_TIMEOUT_SEC = 30
POLL_INTERVAL_SEC = 0.5


def _parse_domain(domain: str) -> tuple[str, int]:
    """Return (host, port) from domain like 'localhost:8080'."""
    if ":" in domain:
        host, _, port_str = domain.rpartition(":")
        return host or "localhost", int(port_str)
    return domain, 8080


def _server_reachable(domain: str) -> bool:
    """Return True if the OpenSandbox server is reachable (port open or GET succeeds)."""
    host, port = _parse_domain(domain)
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except (socket.error, OSError):
        return False


def _docker_available() -> bool:
    """Return True if Docker daemon is reachable (so opensandbox-server can use it)."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _start_server(config_path: str) -> subprocess.Popen | None:
    """Start opensandbox-server in the background. Returns the Popen instance or None on failure."""
    config_path = os.path.expanduser(config_path)
    if not os.path.isfile(config_path):
        logger.warning("OpenSandbox config not found: %s (run: opensandbox-server init-config ~/.sandbox.toml --example docker)", config_path)
        return None
    cmd = ["opensandbox-server", "--config", config_path]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        return proc
    except Exception as e:
        logger.warning("Failed to start opensandbox-server: %s", e)
        return None


def ensure_opensandbox_server(
    domain: str | None = None,
    config_path: str | None = None,
    start_if_missing: bool = True,
) -> bool:
    """Ensure the OpenSandbox server is running so the benchmark can use it.

    - If the server is already reachable at domain, returns True.
    - If start_if_missing and server is not reachable, tries to start it via
      opensandbox-server (requires Docker to be running).
    - Returns True if the server is reachable (either already or after starting).
    - Returns False if the server is not reachable and we could not start it.

    Args:
        domain: Server address, e.g. 'localhost:8080'. Default from OPENSANDBOX_DOMAIN or 'localhost:8080'.
        config_path: Path to server config TOML. Default ~/.sandbox.toml.
        start_if_missing: If True, try to start the server when not reachable.

    Returns:
        True if server is reachable, False otherwise.
    """
    domain = domain or os.environ.get("OPENSANDBOX_DOMAIN", DEFAULT_DOMAIN)
    config_path = config_path or os.environ.get("SANDBOX_CONFIG_PATH", DEFAULT_CONFIG)

    if _server_reachable(domain):
        logger.info("OpenSandbox server already reachable at %s", domain)
        return True

    if not start_if_missing:
        logger.warning("OpenSandbox server not reachable at %s (start it with: opensandbox-server --config %s)", domain, config_path)
        return False

    if not _docker_available():
        print(
            "Docker is not running. OpenSandbox requires Docker.\n"
            "  - Start Docker Desktop (or Colima/Rancher Desktop), then run the benchmark again.\n"
            "  - Or start the server manually: opensandbox-server --config ~/.sandbox.toml\n",
            file=sys.stderr,
        )
        return False

    logger.info("OpenSandbox server not reachable at %s; attempting to start it...", domain)
    proc = _start_server(config_path)
    if proc is None:
        print(
            "OpenSandbox server could not be started. Ensure Docker is running and run:\n"
            "  opensandbox-server init-config ~/.sandbox.toml --example docker\n"
            "  opensandbox-server --config ~/.sandbox.toml\n",
            file=sys.stderr,
        )
        return False

    deadline = time.monotonic() + READY_TIMEOUT_SEC
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SEC)
        if proc.poll() is not None:
            stderr = (proc.stderr and proc.stderr.read()) or b""
            err = stderr.decode("utf-8", errors="replace").strip() or "exited unexpectedly"
            print(f"OpenSandbox server exited: {err}", file=sys.stderr)
            if b"Docker" in stderr or b"docker" in stderr or b"503" in stderr:
                print("Make sure Docker Desktop (or Colima) is running.", file=sys.stderr)
            return False
        if _server_reachable(domain):
            logger.info("OpenSandbox server started and reachable at %s", domain)
            return True

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("OpenSandbox server did not become reachable in time.", file=sys.stderr)
    return False
