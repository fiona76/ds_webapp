"""
Shared constants and utilities for DS WebApp E2E tests.

Imported by test files and conftest.py alike.
"""

import os
import re
import shutil
from collections import defaultdict

SERVER_PORT = 18095
APP_URL = f"http://localhost:{SERVER_PORT}/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
STEP_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "simplified_CAD.stp"))
LATEST_SCREENSHOTS_DIR = os.path.join(SCREENSHOTS_DIR, "latest")
FAILED_SCREENSHOTS_DIR = os.path.join(SCREENSHOTS_DIR, "failed")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

_SCREENSHOT_INDEX = defaultdict(int)
_SCREENSHOTS_BY_TEST = defaultdict(list)


def _slug(text):
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", text)).strip("_").lower()


def _parse_test_ref(test_ref):
    """Return (test_file_stem, test_function) from nodeid-like test ref."""
    base = test_ref.split(" ", 1)[0]
    if "::" in base:
        file_part, func_part = base.split("::", 1)
    else:
        file_part, func_part = "unknown_test_file.py", "unknown_test"
    file_stem = os.path.splitext(os.path.basename(file_part))[0]
    func_name = func_part.split("[", 1)[0]
    return file_stem, func_name


def _current_test_key():
    current = os.environ.get("PYTEST_CURRENT_TEST", "unknown_test_file.py::unknown_test")
    return _parse_test_ref(current)


def prepare_screenshot_dirs(clean=True):
    """Prepare screenshots/latest and screenshots/failed directories."""
    if clean:
        shutil.rmtree(LATEST_SCREENSHOTS_DIR, ignore_errors=True)
        shutil.rmtree(FAILED_SCREENSHOTS_DIR, ignore_errors=True)
    os.makedirs(LATEST_SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(FAILED_SCREENSHOTS_DIR, exist_ok=True)
    _SCREENSHOT_INDEX.clear()
    _SCREENSHOTS_BY_TEST.clear()


def copy_failed_screenshots(test_nodeid):
    """Copy all screenshots for a failed test from latest/ to failed/."""
    test_key = _parse_test_ref(test_nodeid)
    rel_paths = _SCREENSHOTS_BY_TEST.get(test_key, [])
    for rel_path in rel_paths:
        src = os.path.join(LATEST_SCREENSHOTS_DIR, rel_path)
        dst = os.path.join(FAILED_SCREENSHOTS_DIR, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            shutil.copy2(src, dst)


def screenshot(page, name):
    """Save a screenshot to screenshots/latest/<test_file>/<test_function>/.

    Args:
        page: Playwright page object.
        name: Step label (e.g. "layout_all_open.png", "after_toggle").

    Returns:
        Absolute path to the saved screenshot.
    """
    test_file, test_func = _current_test_key()
    test_key = (test_file, test_func)
    _SCREENSHOT_INDEX[test_key] += 1
    step_num = _SCREENSHOT_INDEX[test_key]

    step_label = _slug(os.path.splitext(name)[0]) or "step"
    filename = f"{step_num:02d}_{step_label}.png"
    rel_dir = os.path.join(test_file, test_func)
    rel_path = os.path.join(rel_dir, filename)
    path = os.path.join(LATEST_SCREENSHOTS_DIR, rel_path)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    page.screenshot(path=path, full_page=False)
    _SCREENSHOTS_BY_TEST[test_key].append(rel_path)
    return path
