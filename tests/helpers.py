"""
Shared constants and utilities for DS WebApp E2E tests.

Imported by test files and conftest.py alike.
"""

import os

SERVER_PORT = 18095
APP_URL = f"http://localhost:{SERVER_PORT}/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
STEP_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "simplified_CAD.stp"))

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def screenshot(page, name):
    """Save a screenshot to the screenshots/ directory.

    Args:
        page: Playwright page object.
        name: Filename (e.g. "layout_all_open.png").

    Returns:
        Absolute path to the saved screenshot.
    """
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.screenshot(path=path, full_page=False)
    return path
