# DS WebApp

Trame-based web app for thermal-stress simulation. Sub-models are generated once; after that, changing boundary conditions or power maps is fast.

**Tech stack:** Python, trame, VTK/vtk.js, OCP (STEP import).

## Product flow contract (shared-link entry)

- Primary usage starts when a user opens a shared link.
- First screen is a project-start prompt:
  - `Create New Project`
  - `Open Saved Project`
- First-time users can start with a blank project and save later. Returning users can open a saved project to continue.
- After a new blank project is created, the working layout/panels follow `ui_behavior.md`.
- Geometry input supports both demo examples and user-provided local geometry.
- Materials flow supports:
  - creating blank materials and filling catalog/properties
  - loading default materials and editing them for the project
- Project save/load must preserve resume fidelity. Saved payload includes:
  - geometry source reference(s) (local path or demo pointer)
  - materials JSON
  - netlist
  - `geom`
  - boundary conditions (`BC`)
  - simulation result artifact (`VTM`) when available

## How to run

```bash
python -m app.main                    # start the app
.venv/bin/pytest tests/ -q            # run all tests (~5 min)
.venv/bin/pytest tests/test_local_adapter.py -vv  # unit tests only (<1s)
```

## Where to put code

```
app/
  ui/                # trame widgets, layout, state bindings (one file per panel)
    layout.py        # top-level layout (composes all panels)
    model_builder.py # Model Builder tree + handlers
    settings_panel.py # context-sensitive Settings panel
    viewer.py        # 3D VTK viewport
    log_panel.py     # bottom log panel
    menu_bar.py      # File / Edit menus
  engine/            # simulation logic — NO trame dependency
    geometry.py      # STEP file import and tessellation
  state/
    keys.py          # central registry of all trame state key names
integration/
  local_adapter.py   # BC business logic (exclusivity, assignment, sync)
  dto.py             # response dataclasses
  api.py             # integration API interface
tests/               # see verification.md for test guide
```

Future `engine/` files (add as features are built): `materials.py`, `boundary.py`, `modelization.py`, `builder.py`, `solver.py`, `results.py`, `project.py`.

**Rules:**
1. **Engine has zero UI dependency.** Everything in `engine/` must be callable from a script without trame. Write the engine function first, then wire the UI to call it.
2. **One UI file per panel.** To change the Settings panel, open `settings_panel.py`. Don't put panel logic in `layout.py`.
3. **State keys go in `keys.py`.** Never use raw state key strings. Import the constant from `keys.py`. When adding a new key, add it there first.
4. **Don't save files outside this repo** (`/home/fiona-wang/Documents/ds_webapp`) unless explicitly asked.
5. **UI talks to backend through the integration layer only.** Never call `engine/` directly from `ui/`. The path is always: `ui/` → `integration/adapter` → `engine/` (or remote backend).
6. **Every new backend operation needs three things:** a method in `api.py` (Protocol), a response type in `dto.py`, and an implementation in `local_adapter.py`. A future `RemoteBackendAdapter` will implement the same Protocol.
7. **Return DTOs, not raw dicts.** Adapter methods return typed dataclasses from `dto.py` so the UI code has a stable contract regardless of which adapter is behind it.

## State keys reference

All trame state keys are defined in `app/state/keys.py`. UI and engine code import from here.

| Constant | Value | Purpose |
|---|---|---|
| `SHOW_LEFT_PANELS` | `"show_left_panels"` | Toggle both left panels |
| `SHOW_SETTINGS` | `"show_settings"` | Toggle Settings panel |
| `SHOW_LOG_PANEL` | `"show_log_panel"` | Toggle Log panel |
| `ACTIVE_NODE` | `"active_node"` | Selected tree node ID |
| `SELECTED_OBJECT` | `"selected_object"` | Highlighted object name (null = none) |
| `LOG_MESSAGES` | `"log_messages"` | Log panel message list |
| — | `"viewer_show_edges"` | Mesh edge visibility (default: true) |
| — | `"viewer_semi_transparent"` | 40% opacity mode (default: false) |
| — | `"viewer_wireframe"` | CAD feature edge visibility (default: true) |
| — | `"viewer_scene_light"` | Scene lighting on/off (default: true) |
| `BC_POWER_SOURCES` | `"bc_power_sources"` | Power source items `[{id, name, assigned_objects, power}]` |
| `BC_TEMPERATURES` | `"bc_temperatures"` | Temperature items `[{id, name, assigned_surfaces, temperature}]` |
| `BC_POWER_SOURCE_COUNTER` | `"bc_power_source_counter"` | Auto-increment counter |
| `BC_TEMPERATURE_COUNTER` | `"bc_temperature_counter"` | Auto-increment counter |
| — | `"bc_editing_id"` | BC item being renamed inline |
| — | `"bc_editing_name"` | Current inline rename text |
| — | `"browse_current_dir"` | File browser current directory |
| — | `"browse_entries"` | File browser entries list |

When adding a new state key: add to `keys.py` first, then import everywhere, then add to the reset block in `tests/conftest.py`.

## Pitfalls

These are hard-won lessons. Read before touching viewer or trame code.

- **VTK version:** `cadquery-ocp==7.7.2` bundles VTK 9.2.6. The standalone `vtk` must be `9.3.0` (installed `--no-deps`). Do NOT upgrade to `vtk>=9.4` — it breaks `vtkWebCore`.
- **VtkLocalView is client-side only.** Server-side VTK calls (`renderer.ResetCamera()`, `SetRepresentationToWireframe()`) do NOT propagate to the browser. Use `view.reset_camera()` to sync camera, `view.update()` to re-render. See `learning.md` Learning 1 for the full serializer caching issue.
- **Trame event modifiers:** `keyup_enter=(handler, "[]")` does NOT map to Vue's `@keyup.enter`. Workaround: use `__properties` to inject Vue directives directly: `v_on_keyup_enter="$event.target.blur()"` with `__properties=[("v_on_keyup_enter", "v-on:keyup.enter")]`.
- **Trame v_model race condition:** When `v_model` state update and event callback fire simultaneously, the server may get the event first. Always pass the value as a callback argument: `blur=(handler, "[bc_editing_name]")` instead of reading `state.bc_editing_name` inside the handler.
- **Never rebuild VTK actors for the same geometry data.** This triggers the PROP_CACHE aliasing bug (see `learning.md` Learning 1). Use the `_displayed_objects_id` guard in `viewer.py`.

## Other docs

| File | What it covers |
|------|---------------|
| `ui_behavior.md` | Expected UI behavior for all features (layout, import, BC, viewport, workflow) |
| `verification.md` | How to run tests, where to add tests, test fixtures, known issues |
| `learning.md` | Technical lessons learned (VtkLocalView serializer bug, geometry switching) |
