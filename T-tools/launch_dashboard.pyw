"""
KritiKaal Dashboard — 1-Click Launcher
File: T-tools/launch_dashboard.pyw

Runs under pythonw.exe (zero console window — ever).

Behaviour:
  - If the dashboard is already running on port 8501, open/switch to it immediately.
  - If not running, show a Windows balloon notification, launch Streamlit in the
    background (completely hidden), poll until the server is ready, then open the
    browser.
  - If startup times out, show an error notification.

No extra packages required beyond what is already in the venv.
"""

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE        = Path(__file__).resolve().parent          # T-tools/
_VENV_SCRIPTS = _HERE.parent / "venv" / "Scripts"
_PYTHONW     = _VENV_SCRIPTS / "pythonw.exe"
_STREAMLIT   = _VENV_SCRIPTS / "streamlit.exe"
_DASHBOARD   = _HERE / "dashboard.py"

PORT = 8501
URL  = f"http://localhost:{PORT}"

# Windows process creation flags
_CREATE_NO_WINDOW = 0x08000000
_DETACHED_PROCESS = 0x00000008

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_running() -> bool:
    """Return True if something is already listening on PORT."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("localhost", PORT)) == 0


def _notify(title: str, body: str, duration_ms: int = 4000) -> None:
    """
    Show a Windows balloon notification using System.Windows.Forms.
    Spawned as a hidden background process — does not block the launcher.
    """
    ps_cmd = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Application
$n.BalloonTipTitle = '{title}'
$n.BalloonTipText  = '{body}'
$n.Visible = $true
$n.ShowBalloonTip({duration_ms})
Start-Sleep -Milliseconds {duration_ms + 500}
$n.Dispose()
"""
    subprocess.Popen(
        ["powershell", "-NonInteractive", "-WindowStyle", "Hidden",
         "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        creationflags=_CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _launch_streamlit() -> None:
    """Start Streamlit as a fully detached, windowless background process."""
    subprocess.Popen(
        [
            str(_STREAMLIT), "run", str(_DASHBOARD),
            "--server.port",              str(PORT),
            "--server.headless",          "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType",   "none",   # no hot-reload watcher needed
        ],
        cwd=str(_HERE),
        creationflags=_DETACHED_PROCESS | _CREATE_NO_WINDOW,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_for_server(timeout_s: int = 35) -> bool:
    """Poll PORT until it opens. Returns True if ready, False if timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _is_running():
            return True
        time.sleep(0.8)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if _is_running():
        # Already up — just open (browser will switch to existing tab)
        webbrowser.open(URL)
        return

    # Validate paths before attempting launch
    if not _STREAMLIT.exists():
        _notify(
            "KritiKaal — Error",
            f"streamlit.exe not found in venv. Re-activate your virtual environment.",
        )
        return

    _notify("KritiKaal", "Dashboard is starting\u2026 (first launch may take ~10s)")
    _launch_streamlit()

    if _wait_for_server():
        webbrowser.open(URL)
    else:
        _notify(
            "KritiKaal — Error",
            "Dashboard did not start within 35 seconds. Check the venv is active.",
            duration_ms=6000,
        )


main()
