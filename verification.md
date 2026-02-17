# Testing Guide

## How to run tests

```bash
# Run all tests (~5 min, needs Playwright Chromium)
.venv/bin/pytest tests/ -q

# Run one file
.venv/bin/pytest tests/test_layout.py -vv

# Run unit tests only (no server/browser, <1s)
.venv/bin/pytest tests/test_local_adapter.py -vv
```

If Playwright fails with browser errors: `.venv/bin/playwright install chromium`

## Where to add tests

| File | What goes here |
|------|----------------|
| `test_layout.py` | Panel visibility, collapse/expand, menu bar |
| `test_geometry_import.py` | Import dialog, STEP file loading, import rows in Settings |
| `test_click_to_pick.py` | Viewport object picking, selection, deselection |
| `test_viewer_modes.py` | Toolbar toggle buttons (mesh edges, transparency, feature edges, lighting) |
| `test_boundary_condition.py` | BC tree nodes, power source / temperature items, assignment, highlight |
| `test_local_adapter.py` | Business logic that doesn't need a browser (exclusivity rules, adapter methods) |

**Adding a new feature area** (e.g., Materials, Modelization): create a new `tests/test_<feature>.py` file. pytest discovers `test_*.py` files automatically.

## How tests work

All fixtures live in `tests/conftest.py` — pytest discovers this file automatically, no imports needed.

- **`page`** — Use this for UI-only tests. Each test gets a fresh browser tab with all trame state keys reset to defaults. If you add a new state key to the app, add it to the reset block in `conftest.py` or it will leak between tests.
- **`imported_geometry`** — Use this for tests that need 3D objects in the viewport. Builds on `page` by importing `tests/data/simplified_CAD.stp` (3 solids: PCB_OUTLINE, CHIP, 3DVC) via trame state trigger. Never click through the import dialog UI in tests — it's slow and flaky.
- **Screenshots** — Use `helpers.screenshot(page, "label.png")` for all screenshots. Saves to `screenshots/latest/<test_file>/<test_func>/01_label.png` with auto-incrementing prefix. Failed test screenshots are copied to `screenshots/failed/`.

## Rules

1. Use `page` or `imported_geometry` fixture — never start your own server or browser.
2. New state keys must be added to the reset block in `conftest.py`.
3. Use `helpers.screenshot()` for screenshots — don't save to custom paths.
4. Use `helpers.STEP_FILE` for the test STEP file path.
5. For viewport picking, use retry sampling (see `_try_pick_any_object` in existing tests) — single clicks are unreliable in headless vtk.js.
