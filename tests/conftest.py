"""
Shared pytest fixtures for DS WebApp E2E tests.

Provides:
  - server:            Session-scoped trame server (started once, shared by all tests)
  - browser:           Session-scoped headless Chromium instance
  - page:              Function-scoped fresh browser page (clean state per test)
  - imported_geometry: Function-scoped page with STEP geometry already loaded

Usage:
    pytest tests/ -v              # run all tests
    pytest tests/test_layout.py -v  # run one file
    pytest tests/ -v -s           # run with print output visible
"""

import os
import signal
import subprocess
import sys
import time

import pytest
from playwright.sync_api import sync_playwright

from helpers import SERVER_PORT, APP_URL, STEP_FILE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server():
    """Start the trame app server once for the entire test session.

    The server runs as a subprocess on port 18095. It is started before
    the first test and killed after the last test finishes.
    """
    # Kill any leftover process on the port
    os.system(f"lsof -ti :{SERVER_PORT} 2>/dev/null | xargs -r kill -9 2>/dev/null")
    time.sleep(0.5)

    proc = subprocess.Popen(
        [sys.executable, "-m", "app.main", "--server", "--port", str(SERVER_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
        cwd=os.path.dirname(os.path.dirname(__file__)),  # ds_webapp root
    )

    # Wait for server to become ready (up to 30 seconds)
    import urllib.request
    for _ in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen(APP_URL, timeout=2)
            break
        except Exception:
            pass
    else:
        proc.kill()
        raise RuntimeError(f"Server did not start on port {SERVER_PORT} within 30s")

    yield proc

    # Teardown: kill the server process group
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


@pytest.fixture(scope="session")
def browser(server):
    """Launch a headless Chromium browser once for the entire test session.

    Depends on `server` to ensure the app is running before any browser
    tests start.
    """
    pw = sync_playwright().start()
    br = pw.chromium.launch(headless=True)
    yield br
    br.close()
    pw.stop()


@pytest.fixture
def page(browser):
    """Create a fresh browser page for each test.

    Each page navigates to the app URL, waits for Vuetify to render,
    then resets shared server state (dialogs, selections, BC items)
    so tests start from a clean slate.

    NOTE: trame shares server state across all WebSocket connections.
    A previous test may have opened a dialog or added items — we must
    reset that state before each test.
    """
    pg = browser.new_page(viewport={"width": 1400, "height": 900})
    pg.goto(APP_URL)
    pg.wait_for_timeout(3000)

    # Reset shared server state to defaults
    pg.evaluate("""() => {
        const s = window.trame.state;
        s.set("show_import_dialog", false);
        s.set("active_node", null);
        s.set("selected_object", null);
        s.set("bc_power_sources", []);
        s.set("bc_temperatures", []);
        s.set("bc_power_source_counter", 0);
        s.set("bc_temperature_counter", 0);
        s.set("bc_editing_id", "");
        s.set("bc_editing_name", "");
        s.set("geometry_imports", []);
        s.set("geometry_import_counter", 0);
        s.set("viewer_show_edges", true);
        s.set("viewer_semi_transparent", false);
        s.set("viewer_wireframe", true);
        s.set("viewer_scene_light", true);
    }""")
    pg.wait_for_timeout(500)

    yield pg
    pg.close()


@pytest.fixture
def imported_geometry(page):
    """A page with STEP geometry already imported and visible.

    Use this fixture for tests that need 3D objects in the viewport
    (viewer modes, click-to-pick, etc.). It imports simplified_CAD.stp
    which contains 3 solid objects: PCB_OUTLINE, CHIP, 3DVC.

    Returns the page object (same as the `page` fixture, but with
    geometry loaded).
    """
    # Expand Geometry node and trigger import
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)

    # Set file path via trame state and click import
    page.evaluate(f'window.trame.state.set("import_file_path", "{STEP_FILE}")')
    page.wait_for_timeout(300)
    page.locator(".import-confirm-btn").click()
    page.wait_for_timeout(5000)  # STEP parsing takes a few seconds

    # Click the import node to show objects in Settings
    page.locator("text=Import 1").first.click()
    page.wait_for_timeout(1000)

    return page
