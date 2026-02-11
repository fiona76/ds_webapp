# DS WebApp — Thermal-Stress Simulation Platform

## Project Overview

A **trame**-based web application for thermal-stress simulation. The key differentiator of this simulator is that **sub-models only need to be generated once**; after generation, users can change boundary conditions or power maps and system solving is very fast.

**Tech stack:** Python, trame (vtk-based web framework), VTK/ParaView for 3D visualization.

---

## Application Layout

### Top Menu Bar
| Menu | Items |
|------|-------|
| **File** | New, Open, Save, Save As |
| **Edit** | Undo, Redo, Select All, Clear Selection |

### Left Panels (collapsible, side-by-side)

1. **Model Builder** (leftmost) — tree/outline with these top-level items:
   - Geometry (expandable — contains Import children)
   - Boundary Condition (expandable — contains Power Source and Temperature leaf nodes)
     - Power Source (leaf node — click to see/manage items in Settings)
     - Temperature (leaf node — click to see/manage items in Settings)
   - Materials
   - Modelization
   - Build Sub-Model
   - Solving
   - Result

   > **Note:** Power Source and Temperature items (Power Source 1, 2, …) are managed **only in the Settings panel**, not as tree children. The tree shows only the two category nodes.

2. **Settings** (right of Model Builder) — context-sensitive panel that displays properties/options for whichever item is selected in the Model Builder tree.

### Center Area
- 3D viewport for rendering VTU results and geometry previews.
- **Viewport toolbar** sits above the viewport with toggle buttons (see below).

### Viewport Toolbar

The toolbar above the 3D viewport contains panel toggle buttons (left-arrow, gear, console) and four **display mode toggles**:

| # | Icon | State Key | Default | Behavior |
|---|------|-----------|---------|----------|
| 1 | `mdi-grid` | `viewer_show_edges` | ON | Shows/hides **triangle mesh edges** on surface actors. This controls VTK's `SetEdgeVisibility()`. |
| 2 | `mdi-circle-half-full` | `viewer_semi_transparent` | OFF | Sets surface opacity to 40%. When an object is selected, the selected object stays solid (100%) while others become semi-transparent. |
| 3 | `mdi-cube-outline` | `viewer_wireframe` | **ON** | Shows/hides **CAD feature edge** line actors — real geometric edges extracted from STEP BRep topology (not triangle mesh wireframe). ON by default so geometry always shows CAD edge outlines. |
| 4 | `mdi-lightbulb-outline` | `viewer_scene_light` | ON | Toggles **scene lighting**. ON = normal shading (ambient 0.2, diffuse 0.8). OFF = flat/ambient-only coloring (ambient 1.0, diffuse 0.0). |

**Key design decisions:**
- **All four toggles are independent** — any combination can be active simultaneously.
- **Icon 1 (mesh edges) and icon 3 (feature edges) are different things.** Icon 1 shows the triangulation mesh on surfaces. Icon 3 shows actual CAD boundary edges (e.g., the 12 edges of a cube) as separate line actors.
- **Feature edges are ON by default** — CAD edge lines are always visible when geometry loads. Users can toggle them off with icon 3.
- **Feature edges are extracted from BRep topology** at import time using `TopExp_Explorer(shape, TopAbs_EDGE)` + `BRepAdaptor_Curve` + `GCPnts_TangentialDeflection`. They are stored as polylines in each object dict and rendered as VTK line actors with `vtkLine` cells.
- **No VTK wireframe representation** — `SetRepresentationToWireframe()` does not work in `VtkLocalView` (vtk.js). All wireframe-like display uses separate line actors instead.
- Feature edge actors use dark color by default (`EDGE_DEFAULT`) and highlight color (`EDGE_HIGHLIGHT`) for the selected object.

### Viewport Controls

- **Reset view button** (`mdi-fit-to-screen-outline`) — floating button at the **bottom-left** of the viewport. Resets camera to fit all geometry. Calls `renderer.ResetCamera()` (server-side bounds recompute) followed by `view.reset_camera()` (client-side VtkLocalView sync).

> **Known pitfall:** `renderer.ResetCamera()` alone does NOT work — it only updates the server-side VTK camera, which doesn't propagate to vtk.js in `VtkLocalView`. You must also call `view.reset_camera()` (registered as `server.controller.view_reset_camera`) to push the camera state to the client. Similarly, `view_update()` only re-renders the current client camera — it does not sync a new camera position from the server.

### STEP File Import Dialog

The import dialog uses a **server-side file browser** (not a simple text field):
- **Path bar** at the top shows the current directory with an editable text field and an **up-arrow** button to navigate to the parent directory.
- **Directory listing** shows folders (with `mdi-folder` icon) and `.step`/`.stp` files (with `mdi-file-cad-box` icon). Sorted: directories first, then files. Hidden files/directories (starting with `.`) are excluded.
- **Click a folder** to navigate into it. **Click a file** to select it (highlighted in blue).
- **"Selected:" label** at the bottom shows the full path of the selected file.
- **Import button** is disabled until a file is selected.
- The path text field can also be edited directly to jump to any directory.

### Bottom Panel
- **Log Panel** — prints underlying commands and status messages as operations run.

---

## Workflow

1. **File > New** — start a new project.
2. **Geometry import** — right-click in Model Builder to import 1..N STEP files. Each appears as `Import 1`, `Import 2`, … under the Geometry node.
3. **Object settings** — click an import entry; the Settings panel shows object name and material assignment.
4. **Materials** — adjust per-material properties (thermal conductivity x/y/z, etc.). In the Settings panel, users can right-click to import a JSON file to load material properties in bulk.
5. **Boundary Conditions** — expand Boundary Condition in the tree. Under it, click Power Source or Temperature to add items (Power Source 1, Temperature 1, etc.). Each item's name is editable. Parameters will be configured per item.
6. **Modelization** — choose parameters for dividing the design into N sub-models.
7. **Build Sub-Model** — select **FVM model** or **AI model** to generate sub-models. Mesh is automatic. Models are saved to a server-side destination folder.
   - *Future:* user selects regions and assigns FVM vs AI per region.
   - *Future:* user-adjustable mesh settings.
8. **Solving** — click Run.
9. **Result** — select a completed simulation; VTU file renders in the center viewport.

---

## Architecture Guidelines

### Separation of Concerns
- **UI layer** (trame widgets, layout, state bindings) — lives in `app/ui/`.
- **Engine layer** (simulation logic, sub-model generation, solving) — lives in `app/engine/`. Must be callable without any UI. This allows headless/batch runs and unit testing.
- **State management** — single trame shared state; UI components read/write through well-defined state keys.

### Directory Structure (target)
```
ds_webapp/
  app/
    __init__.py
    main.py              # entry point, trame server setup
    ui/
      __init__.py
      layout.py           # top-level layout (menu, panels, viewport, log)
      model_builder.py    # Model Builder tree panel
      settings_panel.py   # context-sensitive Settings panel
      log_panel.py        # bottom log panel
      menu_bar.py         # File / Edit menus
      viewer.py           # 3D VTK viewport
    engine/
      __init__.py
      project.py          # project state (new/open/save/save-as)
      geometry.py         # STEP file import and management
      materials.py        # material definitions and property storage
      boundary.py         # boundary condition definitions (power source + temperature)
      modelization.py     # sub-model partitioning logic
      builder.py          # sub-model generation (FVM / AI dispatch)
      solver.py           # solving orchestration
      results.py          # result loading and VTU management
    state/
      __init__.py
      keys.py             # central registry of trame state key names
  tests/
    data/                # sample STEP files, JSON fixtures for tests
      simplified_CAD.stp # reference STEP file (5 objects: NV_MODULE, PCB_OUTLINE, CHIP, simplified_CAD, 3DVC)
  screenshots/
  requirements.txt
  CLAUDE.md
  PROGRESS.md
```

### Why This Structure

**Three packages under `app/` — `ui/`, `engine/`, `state/`:**

- **`ui/`** — One file per visual region of the app (menu bar, model builder panel, settings panel, viewer, log panel) plus `layout.py` that composes them. This means when you need to change what the Settings panel looks like, you open exactly one file (`settings_panel.py`). Each UI file is small and self-contained, which makes it easy to iterate on individual panels without touching unrelated code.

- **`engine/`** — All simulation logic lives here with **zero dependency on trame or any UI framework**. Each file maps to one step in the workflow (geometry import, materials, boundary conditions, modelization, building, solving, results). This separation is the most important design decision because:
  1. You can run the full simulation pipeline from a script or notebook without launching the web app (useful for batch runs, debugging, or a future CLI).
  2. Unit tests can exercise engine logic directly without spinning up a browser.
  3. If trame is ever replaced or a second frontend is added (e.g., a REST API), the engine code doesn't change at all.
  4. Each engine module can be developed and tested independently — `geometry.py` doesn't need `solver.py` to exist yet.

- **`state/keys.py`** — A single file that names every trame state key (e.g., `SHOW_MODEL_BUILDER = "show_model_builder"`). This prevents typo bugs where `ui/layout.py` writes `"show_model_bilder"` and `ui/model_builder.py` reads `"show_model_builder"`. With a central registry, both sides import the same constant, and any rename is a one-line change.

**One UI file per panel (not one giant layout file):**

- The layout has five distinct visual regions that evolve independently. Putting them all in one file would create a 500+ line file where a change to the log panel risks breaking the menu bar. Splitting by panel keeps each file under ~80 lines and lets multiple features be developed in parallel without merge conflicts.

**Engine files mirror the workflow steps:**

- `geometry.py` → `materials.py` → `boundary.py` → `modelization.py` → `builder.py` → `solver.py` → `results.py` follows the exact same order as the Model Builder tree. When a user reports a bug in "Build Sub-Model", you know to look in `engine/builder.py`. This 1:1 mapping between UI tree nodes and engine modules eliminates guesswork about where code lives.

**`tests/` at root level (not inside `app/`):**

- Keeps test code completely separate from production code, so tests are never accidentally shipped or imported. Standard Python convention that works well with pytest discovery.

### State Keys Reference (`app/state/keys.py`)

All trame shared-state keys are defined in one file. UI and engine code should import from here — never use raw strings.

| Constant | Value | Purpose |
|---|---|---|
| `SHOW_LEFT_PANELS` | `"show_left_panels"` | Toggle visibility of both left panels (Model Builder + Settings) |
| `SHOW_SETTINGS` | `"show_settings"` | Toggle visibility of Settings panel |
| `SHOW_LOG_PANEL` | `"show_log_panel"` | Toggle visibility of bottom Log panel |
| `ACTIVE_NODE` | `"active_node"` | Currently selected tree node ID in Model Builder |
| `SELECTED_OBJECT` | `"selected_object"` | Name of highlighted geometry object in viewport (null = none) |
| `LOG_MESSAGES` | `"log_messages"` | List of log strings displayed in the Log panel |
| — | `"viewer_show_edges"` | Toggle mesh edge visibility on surface actors (default: true) |
| — | `"viewer_semi_transparent"` | Toggle 40% opacity on surfaces (default: false) |
| — | `"viewer_wireframe"` | Toggle CAD feature edge line actor visibility (default: true) |
| — | `"viewer_scene_light"` | Toggle scene lighting shaded vs flat (default: true) |
| `BC_POWER_SOURCES` | `"bc_power_sources"` | List of power source items `[{id, name}]` |
| `BC_TEMPERATURES` | `"bc_temperatures"` | List of temperature items `[{id, name}]` |
| `BC_POWER_SOURCE_COUNTER` | `"bc_power_source_counter"` | Auto-increment counter for power source IDs |
| `BC_TEMPERATURE_COUNTER` | `"bc_temperature_counter"` | Auto-increment counter for temperature IDs |
| — | `"bc_editing_id"` | ID of BC item currently being renamed inline (empty = none) |
| — | `"bc_editing_name"` | Current text value in the inline rename text field |
| — | `"browse_current_dir"` | Current directory in the file browser dialog |
| — | `"browse_entries"` | List of directory/file entries for file browser |

> **Rule:** When adding a new state key, add it to `keys.py` first, then import the constant everywhere it's used. This keeps state naming in sync across all files.

---

## What Is Immune from Future Changes

These decisions are stable and should be built first / built well:

1. **Overall layout skeleton** — top menu bar, left dual-panel (Model Builder + Settings), center viewport, bottom log. This structure won't change even as individual panel contents evolve.
2. **The Model Builder tree structure** — the top-level nodes (Geometry, Boundary Condition, Materials, Modelization, Build Sub-Model, Solving, Result) represent the fundamental simulation workflow. Boundary Condition contains Power Source and Temperature sub-groups. Child items will grow, but the top-level sequence is fixed.
3. **Settings panel as a context-sensitive detail view** — the pattern of "click something in Model Builder, see its details in Settings" is the core interaction model. The *contents* of Settings will change per feature, but the *mechanism* is stable.
4. **Engine / UI separation** — keeping simulation logic decoupled from trame UI is essential regardless of how either side evolves.
5. **Log panel** — a log/console at the bottom is a permanent fixture.
6. **Project file operations** (New / Open / Save / Save As) — standard file lifecycle, won't change.
7. **STEP file import under Geometry** — the import mechanism and per-import object listing is settled.

---

## Milestones

### Milestone 1 — App Shell & Layout ✅
> **Goal:** a running trame app with the full layout skeleton and navigation wiring — no simulation logic yet.

Deliverables:
- [x] Trame app boots and opens in browser
- [x] Top menu bar with File (New/Open/Save/Save As) and Edit (Undo/Redo/Select All/Clear Selection) — handlers can be stubs
- [x] Model Builder panel with the 8 top-level tree nodes (clickable, expandable)
- [x] Settings panel updates its content when a Model Builder item is selected (placeholder content per node)
- [x] Center 3D viewport placeholder (empty VTK render window)
- [x] Bottom log panel that can receive and display messages
- [x] Collapsible behavior on left panels

**Screenshot Verification:**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| App launch | — | All panels visible: Model Builder, Settings, viewport, Log | `layout_all_open.png` |
| Click left-arrow toggle | All panels open | Both left panels collapse, viewport expands | `layout_left_collapsed.png` |
| Click left-arrow + log toggle | All panels open | Only menu bar and viewport remain | `layout_panels_closed.png` |

### Milestone 2 — Geometry Import & Material Assignment

Steps:
1. **Verify & clean up existing STEP import** — move test data to `tests/data/`, fix test to use `simplified_CAD.stp` ✅
2. **3D geometry rendering in viewport** — OCP/XCAF STEP reader, tessellation, assembly transforms, VTK rendering ✅
3. **Object highlight on click** — click object in Settings or viewport to highlight it ✅
4. **Viewport display modes** — mesh edges, semi-transparent, feature edge toggles ✅
5. **Feature edges default ON + scene light toggle + reset view + file browser** ✅
6. **Boundary Condition tree submenu** — Power Source and Temperature under BC, dynamic items, rename ✅
7. **Material definitions engine** — `engine/materials.py` with MaterialLibrary, default materials, thermal conductivity (kx/ky/kz)
8. **Per-object material assignment** — dropdown per object in Settings when an import node is selected
9. **Material property editor UI** — click Materials node → Settings shows editable material list with kx/ky/kz fields
10. **JSON import for bulk material properties** — import button in Materials settings, loads from JSON file

**Screenshot Verification:**

*File Browser & Geometry Import (Steps 1-2, 5):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Click "Import STEP file..." in Geometry context menu | Tree shows only top-level nodes | File browser dialog opens showing home directory | `file_browser_open.png` |
| Navigate to directory with STEP files | Home directory listing | Target directory shown with .stp files listed | `file_browser_navigate.png` |
| Click a .stp file in the list | No file selected, Import disabled | File highlighted blue, "Selected:" shows full path, Import enabled | `file_browser_selected.png` |
| Click "Import" | Dialog with file selected | "Import 1" in tree, geometry renders in viewport | `file_browser_after_import.png` |
| Click "Import 1" node in tree | Settings shows placeholder | Settings shows file info and object list (PCB_OUTLINE, CHIP, 3DVC) | `geometry_import_settings.png` |

*Object Highlight — Settings Panel Click (Step 3):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (initial state after import) | — | All objects default blue in viewport | `highlight_before.png` |
| Click PCB_OUTLINE in Settings list | All objects blue | PCB_OUTLINE turns orange, row highlighted | `highlight_pcb_outline.png` |
| Click CHIP in Settings list | PCB_OUTLINE orange | CHIP orange, PCB_OUTLINE back to blue | `highlight_chip.png` |
| Click CHIP again (deselect) | CHIP orange | All objects back to default blue | `highlight_none.png` |

*Object Highlight — Viewport Click-to-Pick (Step 3):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (initial state) | — | No selection, all objects blue | `pick_before_click.png` |
| Click on an object in viewport | No selection | Object highlighted orange, name label at bottom | `pick_center_click.png` |
| (highlighted state) | — | Selected object orange with label overlay | `pick_highlighted.png` |
| Click empty space in viewport | Object selected | Selection cleared, all objects blue | `pick_deselected.png` |

*Viewport Display Mode Toggles (Steps 4-5):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (default state) | — | Solid surfaces with mesh edges + CAD feature edges, light ON | `feature_edges_default_on.png` |
| Click icon 1 (mesh edges OFF) | Mesh edges visible | Smooth surfaces, no triangle mesh lines | `viewer_mode_no_edges.png` |
| Click icon 2 (semi-transparent ON, no selection) | Solid surfaces | All objects at 40% opacity | `viewer_mode_semi_transparent_all.png` |
| Click object, then icon 2 (semi-transparent with selection) | All semi-transparent | Selected object solid (100%), others 40% opacity | `viewer_mode_semi_transparent_selected.png` |
| Click icon 3 (feature edges OFF) | CAD edge lines visible | CAD edge lines hidden | `viewer_mode_feature_edges.png` |
| Icon 3 ON + icon 1 OFF | Feature edges + mesh edges | Smooth surfaces with only CAD edge lines (no mesh) | `viewer_mode_feature_edges_no_mesh.png` |
| Icon 2 ON + icon 3 ON (combined) | Single mode active | Semi-transparent surfaces + feature edge lines (both active) | `viewer_mode_combined.png` |
| Click icon 4 (scene light OFF) | Normal shaded surfaces | Flat/ambient-only coloring, no light shading | `scene_light_off.png` |
| Click icon 4 again (scene light ON) | Flat coloring | Normal shaded surfaces restored | `scene_light_on.png` |

*Reset View Button (Step 5):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (baseline after import) | — | Geometry centered at default zoom | `reset_view_1_baseline.png` |
| Zoom in with mouse wheel | Default view | Geometry fills viewport (zoomed in) | `reset_view_2_zoomed.png` |
| Click reset view button | Zoomed in | Camera resets to baseline view (0.71% pixel diff from baseline) | `reset_view_3_after_reset.png` |

> **Bug fixed:** Initial implementation called `renderer.ResetCamera()` + `view_update()` — server-side only, camera reset did not propagate to client-side vtk.js. Fixed to call `renderer.ResetCamera()` + `view.reset_camera()` (VtkLocalView client-side method). Verified with automated pixel-diff test (`/tmp/test_reset_view.py`).

*Boundary Condition Tree (Step 6):*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Click "Boundary Condition" | BC collapsed | BC expands showing Power Source and Temperature leaf nodes | `bc_expanded.png` |
| Click "Power Source" | No settings | Settings shows "Power Sources" title + "Add Power Source" button | `bc_power_source_settings.png` |
| Click "Add Power Source" | Empty list | "Power Source 1" appears in Settings list (stays on category view) | `bc_power_source_added.png` |
| Click "Add Power Source" again | One item | Both "Power Source 1" and "Power Source 2" in Settings list | `bc_two_power_sources.png` |
| Double-click "Power Source 1" | Display mode | Inline text field appears; "Power Source 2" stays visible | `bc_rename_editing.png` |
| Type new name + Enter | Editing mode | Name updated to "My Custom Source", both items visible | `bc_rename_done.png` |
| Click "Temperature" | Power Source settings | Settings shows "Temperatures" title + "Add Temperature" button | `bc_temperature_settings.png` |
| Add two temperatures | Empty list | Both "Temperature 1" and "Temperature 2" visible | `bc_temperature_two.png` |

> **Design:** BC items (Power Source 1, 2, …) are managed **only in the Settings panel**. They do NOT appear as children in the Model Builder tree. Adding an item stays on the category view. Renaming is done inline via double-click — all items remain visible during editing.

### Milestone 3 — Build Sub-Model Pipeline
- Modelization parameters UI
- Build Sub-Model with FVM/AI toggle
- Server-side model output to destination folder
- Progress feedback in log panel

> **Screenshot verification required** — capture before/after for: modelization parameter changes, Build Sub-Model button click (progress in log), FVM/AI toggle switch.

### Milestone 4 — Solving & Result Visualization
- Solving run trigger + status
- Result listing under Result node
- VTU file loading and rendering in center viewport

> **Screenshot verification required** — capture before/after for: Solving Run click (progress in log), result node selection, VTU rendering in viewport.

### Milestone 5 — Boundary Condition Parameters (Power Source & Temperature)
- Power Source parameter fields (per item)
- Temperature parameter fields (per item)
- BC effect visualization in viewport

> **Screenshot verification required** — capture before/after for each BC parameter change and its effect on the viewport.

### Milestone 6 — Project Persistence
- Full New / Open / Save / Save As with a project file format

> **Screenshot verification required** — capture before/after for: File > New (clears state), File > Open (loads project), File > Save (confirmation).

---

## Dev Notes

- Run app: `python -m app.main` (once scaffolded)
- trame docs: https://trame.readthedocs.io/
- Target Python >= 3.9
- **VTK version constraint:** `cadquery-ocp==7.7.2` bundles VTK 9.2.6 core modules. The standalone `vtk` package must be `9.3.0` (installed with `--no-deps`) to provide `vtkWebCore` for trame rendering. Do NOT upgrade to `vtk>=9.4` — it will break `vtkWebCore` initialization.
- **VtkLocalView server/client gotcha:** `VtkLocalView` renders entirely client-side in vtk.js. Server-side VTK calls (`renderer.ResetCamera()`, `SetRepresentationToWireframe()`, etc.) do NOT automatically propagate to the client. Use `view.reset_camera()` to sync camera, and `view.update()` to re-render. Never rely on server-side VTK state changes being visible in the browser without an explicit client-side sync call.
- **Trame event modifier limitation:** `keyup_enter=(handler, "[]")` does NOT map to Vue's `@keyup.enter`. Trame cannot translate Python underscore names to Vue event modifiers with dot notation. **Workaround:** Use `__properties` to inject Vue directives directly: `v_on_keyup_enter="$event.target.blur()"` with `__properties=[("v_on_keyup_enter", "v-on:keyup.enter")]`. For inline rename, we use this to blur on Enter, then the `blur` event handler commits the rename.
- **Trame v_model race condition:** When a `v_model` state update and an event callback fire simultaneously, the server may receive the event before the state update. Always pass the current value as an argument to the callback: `blur=(handler, "[bc_editing_name]")` instead of reading `state.bc_editing_name` inside the handler.

### Screenshot Verification Rule

**Agents must perform Playwright screenshot verification for every new feature or UI change.** This is required, not optional. For each user-visible action (clicking a button, importing a file, changing a parameter, toggling a mode), capture **before and after** screenshots and visually confirm the result before marking the task as done.

Requirements:
1. **Before/after pairs** — every clickable action should have a screenshot showing the state before the click and the state after.
2. **Save to `screenshots/`** with descriptive names (e.g., `feature_name_before.png`, `feature_name_after.png`).
3. **Add to the milestone's Screenshot Verification table** in CLAUDE.md (User Action | Before | After | Screenshot).
4. **Automated tests preferred** — write Playwright tests in `tests/` that import the STEP file, perform the actions, capture screenshots, and assert state. This catches regressions automatically.
5. This catches rendering issues that code review alone cannot detect. vtk.js client-side rendering often behaves differently from desktop VTK — always verify visually.

### Regression Test Design

**Every new feature must include regression test considerations.** When adding or modifying a feature:

1. **Identify which existing features could break** — e.g., changing the viewer might break object picking; changing the import dialog might break the import workflow.
2. **Design test cases that verify existing behavior is preserved** — not just new behavior. Run existing Playwright tests after every change.
3. **Test matrix for display toggles** — the four toolbar icons (mesh edges, semi-transparent, feature edges, scene light) have 16 possible on/off combinations. Key combinations should be tested:
   - Default state (edges ON, semi OFF, feature ON, light ON)
   - All OFF, all ON
   - Each toggle individually
   - Semi-transparent + feature edges (combined)
4. **Import flow regression** — after any dialog change, verify: open dialog → navigate → select file → import → geometry renders → objects appear in Settings.
5. **Selection regression** — after any viewer change, verify: click object in Settings → highlights in viewport → click in viewport → highlights → deselect works.
6. **Store golden screenshots** — keep a set of known-good screenshots for visual comparison. When a test produces a different result, flag it for review.

> **Critical:** Always run `tests/test_viewer_modes.py`, `tests/test_geometry_import.py`, and `tests/test_boundary_condition.py` after any change to viewer, layout, model_builder, or settings_panel code.

### Critical Future Task: CLI Backend for All User Actions

**Every user action in the UI must eventually map to a callable engine function.** The long-term goal is that every button click, toggle, file import, parameter change, and solve trigger is backed by a corresponding engine API that can be invoked from a CLI or script without the web UI.

Why this matters:
- Enables batch runs, scripting, and automated pipelines without launching the browser.
- Ensures the engine layer is fully testable without UI dependencies.
- Makes it possible to add a REST API, notebook interface, or second frontend later.

When implementing new features, always:
1. **Write the engine function first** (in `app/engine/`) — pure Python, no trame dependency.
2. **Wire the UI to call the engine function** (in `app/ui/`) — the UI is a thin wrapper.
3. **Document the engine API** so it can be called from a script: `from app.engine.X import Y; Y(args)`.
