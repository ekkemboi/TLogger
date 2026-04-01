"""E2E test fixtures for agent-browser testing."""

import subprocess
import time
import os
import signal

import pytest


@pytest.fixture(scope="session")
def electron_app():
    """Start Electron app with remote debugging for testing."""
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    desktop_dir = os.path.join(project_root, "desktop")

    # Start Electron with remote debugging
    env = os.environ.copy()
    env["ELECTRON_DEV"] = "1"

    proc = subprocess.Popen(
        ["bun", "start"],
        cwd=desktop_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        preexec_fn=os.setsid,  # Create new process group
    )

    # Wait for app to start
    time.sleep(5)

    # Verify app started
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        raise RuntimeError(f"Electron failed to start: {stderr.decode()}")

    yield {"pid": proc.pid, "dir": desktop_dir, "proc": proc}

    # Cleanup: kill process group
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except:
        proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def agent_browser():
    """Provide agent-browser CLI commands."""

    def run_command(args, timeout=30):
        result = subprocess.run(
            ["agent-browser"] + args, capture_output=True, text=True, timeout=timeout
        )
        return result

    return {
        "run": run_command,
        "snapshot": lambda: run_command(["snapshot", "-i"]),
        "screenshot": lambda path: run_command(["screenshot", path]),
    }


@pytest.fixture
def widget_url():
    """URL for widget (Electron loads local file)."""
    return None  # Electron loads file:// internally
