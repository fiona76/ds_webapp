# DS WebApp — Progress Notes

## Milestone 1: App Shell & Layout — COMPLETED

**Date:** 2026-02-09

### Deliverables
- [x] Trame app boots and opens in browser
- [x] Top menu bar with File (New/Open/Save/Save As) and Edit (Undo/Redo/Select All/Clear Selection) — stub handlers log to console
- [x] Model Builder panel with 8 top-level tree nodes (Geometry, Boundary Condition, Power Map, Materials, Modelization, Build Sub-Model, Solving, Result)
- [x] Settings panel updates content when a Model Builder item is selected (placeholder content per node)
- [x] Center 3D viewport (empty VTK render window)
- [x] Bottom log panel that displays messages
- [x] Collapsible left panels (Model Builder, Settings) and log panel via toolbar toggle buttons

### Screenshot Verification

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| App launch | — | All panels visible: Model Builder, Settings, viewport, Log | `layout_all_open.png` |
| Click left-arrow toggle | All panels open | Both left panels collapse, viewport expands | `layout_left_collapsed.png` |
| Click left-arrow + log toggle | All panels open | Only menu bar and viewport remain | `layout_panels_closed.png` |

### Notes
- Toggle buttons are in the viewport toolbar: left-arrow (both left panels), gear (Settings only), console icon (Log)
- Arrow button collapses/expands both Model Builder and Settings together
- Menu items log actions to the bottom Log panel
- Clicking a tree node in Model Builder updates the Settings panel with context-specific placeholder content

### Post-completion fixes
- **Left panel collapse bug** (2026-02-09): arrow button now collapses both Model Builder AND Settings together (was only collapsing Model Builder). Uses `show_left_panels` state key. Verified with `layout_left_collapsed.png`.
- **Title bar layout**: moved "DS WebApp" to white bar above blue menu bar, File/Edit to left of blue bar, title bar height set to 30px.
- **VTK graceful fallback**: viewer shows placeholder text if VTK fails to import.

---

## Milestone 2: Geometry Import & Material Assignment — IN PROGRESS

### Step Plan
| Step | Description | Status |
|------|-------------|--------|
| 1 | Verify & clean up existing STEP import (move test data, fix test) | DONE |
| 2 | 3D geometry rendering in viewport | DONE |
| 3 | Object highlight on click (Settings panel + viewport pick) | DONE |
| 4 | Viewport display modes (mesh edges, semi-transparent, feature edges) | DONE |
| 5 | Feature edges default ON, reset view, scene light, file browser | DONE |
| 6 | Boundary Condition tree submenu (Power Source & Temperature) | DONE |
| 7 | Material definitions engine (`engine/materials.py`) | PENDING |
| 8 | Per-object material assignment dropdown in Settings | PENDING |
| 9 | Material property editor UI | PENDING |
| 10 | JSON import for bulk material properties | PENDING |

### Step 1: Verify & Clean Up Existing Import — DONE

**Date:** 2026-02-10

**Changes:**
- Moved `simplified_CAD.stp` → `tests/data/simplified_CAD.stp`
- Added `tests/data/` convention to CLAUDE.md directory structure
- Updated `tests/test_geometry_import.py` to use new path, absolute path, and `simplified_CAD.stp` objects
- Fixed flaky dialog-close assertion (was matching tree text instead of dialog state)

**Reference file:** `simplified_CAD.stp` — 3 solid objects: PCB_OUTLINE, CHIP, 3DVC (the 2 assembly containers NV_MODULE and simplified_CAD are not geometry)

**Screenshot Verification**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Click "Import STEP file..." in context menu | Tree shows top-level nodes only | Import dialog appears with path input | `geometry_import_dialog.png` |
| Enter path and click "Import" | Dialog open, viewport empty | "Import 1" in tree, geometry renders | `geometry_import_tree.png` |
| Click "Import 1" node | Settings shows placeholder | Settings shows file info + 3 objects | `geometry_import_settings.png` |

**Known issues:**
- Settings panel "File" field renders empty (file name not displayed) — pre-existing display bug from Milestone 1

---

### Step 2: 3D Geometry Rendering in Viewport — DONE

**Date:** 2026-02-10

**Changes:**
- **`engine/geometry.py`** — Replaced regex text parser with OCP/XCAF-based STEP reader. Walks assembly tree via `STEPCAFControl_Reader`, identifies only actual solids (not assembly containers), tessellates faces via `BRepMesh_IncrementalMesh`, and returns vertices + triangles per object. Accumulates and applies placement transforms from the assembly hierarchy so objects are correctly positioned.
- **`ui/viewer.py`** — Switched from `import vtk` (broken by version conflict) to individual `vtkmodules` imports. Added `_objects_to_vtk_polydata()` to convert mesh data to VTK polydata with computed normals. Added `show_geometry()` function registered on controller to render/replace geometry in the viewport.
- **`ui/model_builder.py`** — Stores mesh data server-side (not in trame state — too large for client sync). Passes only object names to UI state. Calls `show_geometry()` on import and when clicking an import node in the tree.
- **VTK dependency fix** — `cadquery-ocp==7.7.2` bundles VTK 9.2.6 without `vtkWebCore`; standalone `vtk==9.5.2` provided `vtkWebCore` but was incompatible (version mismatch). Fixed by installing `vtk==9.3.0 --no-deps` which is compatible with both.
- **Assembly transform bug** — Solids were rendered in their local coordinate frames, ignoring parent assembly placement transforms. Fixed by accumulating `TopLoc_Location` through the XCAF hierarchy and applying to vertices during tessellation.

**Screenshot Verification**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Import STEP file | Viewport empty | 3D geometry visible, 3 stacked layers correctly positioned | `geometry_import_tree.png` |

---

### Step 3: Object Highlight on Click — DONE

**Date:** 2026-02-10

**Changes:**
- **`state/keys.py`** — Added `SELECTED_OBJECT` state key for tracking which object is highlighted.
- **`ui/viewer.py`** — Renders each object as a separate VTK actor (previously merged into one). Added `highlight_object(name)` that turns the selected actor orange and resets others to default blue. Default/highlight colors defined as constants.
- **`ui/settings_panel.py`** — Object list items are now clickable with toggle behavior (click to select, click again to deselect). Selected row shows active state styling via Vuetify.
- **`ui/model_builder.py`** — Added `selected_object` state init, watcher that calls `highlight_object` on change, and auto-clears selection when switching tree nodes.

**Screenshot Verification**

*Settings panel click:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (initial state after import) | — | All objects default blue | `highlight_before.png` |
| Click PCB_OUTLINE in Settings | All blue | PCB_OUTLINE orange, row highlighted | `highlight_pcb_outline.png` |
| Click CHIP in Settings | PCB_OUTLINE orange | CHIP orange, PCB_OUTLINE back to blue | `highlight_chip.png` |
| Click CHIP again (deselect) | CHIP orange | All objects back to default blue | `highlight_none.png` |

*Viewport click-to-pick:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (initial state) | — | No selection, all objects blue | `pick_before_click.png` |
| Click object in viewport | No selection | Object orange, name label at bottom | `pick_center_click.png` |
| (highlighted state) | — | Selected object orange with label | `pick_highlighted.png` |
| Click empty space | Object selected | Selection cleared, all blue | `pick_deselected.png` |

---

### Step 4: Viewport Display Modes & Feature Edge Extraction — DONE

**Date:** 2026-02-10

**Changes:**
- **`engine/geometry.py`** — Added `_extract_edges()` function that extracts real CAD edge curves from STEP BRep topology using `TopExp_Explorer(shape, TopAbs_EDGE)`, `BRepAdaptor_Curve`, and `GCPnts_TangentialDeflection`. Each edge is discretized into a polyline with assembly transforms applied. Edge polylines are returned as an `"edges"` key in each object dict from `parse_step_file()`.
- **`ui/viewer.py`** — Added `_edges_to_vtk_polydata()` helper to convert edge polylines into VTK line cells (`vtkLine`). New `edge_actors` dict stores per-object feature edge line actors alongside existing surface actors. Removed all `SetRepresentationToWireframe()` code (broken in `VtkLocalView`/vtk.js). Icon 3 (`mdi-cube-outline`) now toggles feature edge actor visibility instead.
- **`ui/layout.py`** — Removed mutual-exclusivity JS from semi-transparent and wireframe button click handlers. Icons 2 and 3 are now fully independent toggles.
- **`tests/test_viewer_modes.py`** — Rewritten to test feature edge visibility, combined modes (semi-transparent + feature edges), and removed old mutual-exclusivity assertions.

**Bug fixed:** Icon 3 (wireframe) previously called `SetRepresentationToWireframe()` which produced an empty viewport in `VtkLocalView`. Now uses separate line actors for CAD edges.

**Screenshot Verification**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (default state) | — | Solid surfaces + mesh edges | `viewer_mode_baseline.png` |
| Click icon 1 (mesh edges OFF) | Mesh edges visible | Smooth surfaces, no mesh lines | `viewer_mode_no_edges.png` |
| Click icon 2 (semi-transparent, no selection) | Solid surfaces | All objects 40% opacity | `viewer_mode_semi_transparent_all.png` |
| Select object + icon 2 | All semi-transparent | Selected solid, others 40% | `viewer_mode_semi_transparent_selected.png` |
| Click icon 3 (feature edges ON) | No edge lines | Dark CAD edge lines over surfaces | `viewer_mode_feature_edges.png` |
| Icon 3 ON + icon 1 OFF | Feature + mesh edges | Smooth surfaces + CAD edges only | `viewer_mode_feature_edges_no_mesh.png` |
| Icon 2 ON + icon 3 ON | Single mode | Semi-transparent + feature edges | `viewer_mode_combined.png` |

---

### Step 5: Feature Edges Default ON, Reset View, Scene Light, File Browser — DONE

**Date:** 2026-02-10

**Changes:**
- **Feature edges default ON** — Changed `state.viewer_wireframe` default from `False` to `True` in `viewer.py`. CAD edge lines are now always visible when geometry loads.
- **Reset view button** — Added floating button (`mdi-fit-to-screen-outline`) at bottom-left of viewport. Calls `renderer.ResetCamera()` + `view.reset_camera()` (client-side). Registered as `server.controller.reset_view`.
- **Scene light toggle** — Added icon 4 (`mdi-lightbulb-outline`) to toolbar with `viewer_scene_light` state (default: True). Light ON = normal shading (ambient 0.2, diffuse 0.8). Light OFF = flat/ambient coloring (ambient 1.0, diffuse 0.0). Applied per-actor in `_style_actor()`.
- **File browser dialog** — Replaced text-field import dialog with server-side file browser in `layout.py`:
  - `_refresh_browse_entries()` lists directories and `.step`/`.stp` files (hidden files excluded).
  - Path bar with editable text field and up-arrow button for parent navigation.
  - Clickable VList: folders navigate, files select (highlighted blue).
  - "Selected:" label shows full path. Import button disabled until file selected.
  - State keys: `browse_current_dir`, `browse_entries`, `browse_go_up_trigger`.

**Screenshot Verification**

*Feature edges default ON:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Import geometry (default state) | — | Solid surfaces with mesh edges + CAD feature edges visible | `feature_edges_default_on.png` |

*Scene light toggle:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (default, light ON) | — | Normal shaded surfaces | `scene_light_on.png` |
| Click lightbulb icon (light OFF) | Shaded surfaces | Flat/ambient-only coloring | `scene_light_off.png` |

*Reset view button:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| (baseline after import) | — | Geometry centered at default zoom | `reset_view_1_baseline.png` |
| Zoom in with mouse wheel | Default view | Geometry fills viewport (zoomed) | `reset_view_2_zoomed.png` |
| Click reset view button | Zoomed in | Camera resets to baseline view | `reset_view_3_after_reset.png` |

**Bug fix:** Initial implementation called `renderer.ResetCamera()` + `view_update()` — server-side only, did not propagate to client-side vtk.js. Fixed to call `renderer.ResetCamera()` + `view.reset_camera()` (VtkLocalView client-side method). Verified with pixel-diff test: post-reset matches baseline within 0.71%.

*File browser:*

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Click "Import STEP file..." | Tree only | File browser dialog opens at home directory | `file_browser_open.png` |
| Navigate to directory | Home directory | Target directory with .stp file listed | `file_browser_navigate.png` |
| Click .stp file | No file selected | File highlighted blue, "Selected:" shows path | `file_browser_selected.png` |
| Click Import | File selected | Geometry imported, renders in viewport | `file_browser_after_import.png` |

---

### Step 6: Boundary Condition Tree Submenu — DONE

**Date:** 2026-02-10

**Changes:**
- **Removed "Power Map"** from `MODEL_BUILDER_NODES` — absorbed into Boundary Condition.
- **`app/ui/model_builder.py`** — "Boundary Condition" node now uses `VListGroup` (expandable, collapsed by default) with two leaf children: **Power Source** (`mdi-flash`) and **Temperature** (`mdi-thermometer`). Items are managed only in Settings, not as tree children. Added server-side functions: `add_power_source()`, `add_temperature()`, `rename_bc_item()`, `start_bc_rename()`, `finish_bc_rename()`.
- **`app/ui/settings_panel.py`** — Removed `"power_map"` from `SETTINGS_CONTENT`. Added two Settings sections:
  - `bc_power_source` → "Power Sources" title + item list with inline rename + "Add Power Source" button
  - `bc_temperature` → "Temperatures" title + item list with inline rename + "Add Temperature" button
- **`app/state/keys.py`** — Added `BC_POWER_SOURCES`, `BC_TEMPERATURES`, `BC_POWER_SOURCE_COUNTER`, `BC_TEMPERATURE_COUNTER`.
- **`tests/test_boundary_condition.py`** — Playwright test covering: tree structure, add items (stays on category), inline rename with all items visible, temperature flow.

**Design decisions:**
- BC items (Power Source 1, 2, …) appear **only in Settings**, not as Model Builder tree children.
- Adding an item stays on the category view — no navigation to individual item.
- Renaming is done **inline** via double-click: the item name becomes an editable text field while all other items remain visible.
- Enter key commits rename (via `v-on:keyup.enter` → blur → server callback), click-away also commits.
- State keys: `bc_editing_id` (which item is being edited) and `bc_editing_name` (current text field value).

**Bugs fixed:**
- `keyup_enter` trame binding does NOT map to Vue `@keyup.enter`. Fixed with `__properties=[("v_on_keyup_enter", "v-on:keyup.enter")]` and client-side blur trigger.
- `v_model` race condition: server receives event callback before state update. Fixed by passing `bc_editing_name` as argument to `finish_bc_rename`.

**Screenshot Verification**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Click Boundary Condition | BC collapsed | Expands to show Power Source + Temperature | `bc_expanded.png` |
| Click Power Source | — | Settings: "Power Sources" + Add button | `bc_power_source_settings.png` |
| Click Add Power Source | Empty list | "Power Source 1" in Settings (stays on category) | `bc_power_source_added.png` |
| Add second Power Source | 1 item | Both "Power Source 1" + "Power Source 2" visible | `bc_two_power_sources.png` |
| Double-click "Power Source 1" | Display mode | Inline text field; "Power Source 2" still visible | `bc_rename_editing.png` |
| Type new name + Enter | Editing | "My Custom Source" renamed, both items visible | `bc_rename_done.png` |
| Click Temperature + Add two | — | Both "Temperature 1" + "Temperature 2" visible | `bc_temperature_two.png` |

---

### Step 6B: Boundary Condition Assignment Panels (Object/Surface) — DONE

**Date:** 2026-02-11

**Changes:**
- **Expandable BC rows in Settings** for each `Power Source N` and `Temperature N`.
- Expand/collapse can be triggered by clicking **row text** or chevron icon (improved discoverability).
- **Per-item numeric inputs**:
  - Power Source: `Power (W/m)` default `0`
  - Temperature: `Temperature (oC)` default `0`
- **Single assignment list box per item** with row selection + `+ / -` controls:
  - `-` removes currently selected assigned row.
  - `+` opens placeholder dialog ("not implemented yet" for custom assignment flow).
- Assignment list box uses fixed height with vertical scrolling for long lists; item rows use smaller text and tighter spacing.
- **Viewport click assignment** tied to expanded row:
  - Expanded Power Source row => clicking object toggles assignment (`ObjectName`).
  - Expanded Temperature row => clicking CAD face toggles assignment (`ObjectName:Face-N`).

---

## Milestone 7: Integration Adapter Layer (Local-first, Backend-ready) — PLANNED

**Date added:** 2026-02-12

### Goal
- Introduce a stable integration contract between UI and domain logic now, while the massive backend is still in progress.
- Keep current development velocity with a local adapter.
- Enable a later backend switch with minimal/no UI handler rewrites.

### Why now
- Current BC/domain mutations are implemented directly in `app/ui/model_builder.py` via trame state.
- This works for rapid iteration but increases long-term integration risk (state divergence, duplicated validation, harder sync before simulation).
- Adapter-first migration gives a controlled write path and explicit sync points.

### Target structure (inside this repo for now)
```text
integration/
  __init__.py
  dto.py                  # request/response payload models (typed contracts)
  api.py                  # adapter interface / method signatures
  local_adapter.py        # current implementation using local state + app.engine
  factory.py              # get_adapter(mode="local" | "remote")
  sync.py                 # sync policy helpers (dirty/unsynced flags, pre-run sync gate)
```

### Step plan
| Step | Description | Status |
|------|-------------|--------|
| 1 | Add `integration/dto.py` contracts (OperationResult, BC requests/responses) | DONE |
| 2 | Add `integration/api.py` interface for BC actions (`add/delete/rename/set/assign/unassign`) | DONE |
| 3 | Add `integration/local_adapter.py` and wire current BC UI handlers to it | DONE |
| 4 | Add local state sync markers (`project_dirty`, `project_unsynced`, `project_version`) | PENDING |
| 5 | Add pre-run gate: simulation start must call adapter sync check first | PENDING |
| 6 | Move BC validation/mutation rules out of UI file into engine/service helpers | PENDING |
| 7 | Add contract tests for adapter methods (no UI) | PENDING |
| 8 | Add `integration/remote_adapter.py` skeleton (same interface, `NOT_IMPLEMENTED`) | PENDING |
| 9 | Switchable adapter factory (env/config driven) | PENDING |
| 10 | Update docs (`AGENTS.md`, `CLAUDE.md`, `verification.md`) after adapter wiring | PENDING |

### Initial method signatures (v1 contract)
- `add_power_source(project_id, name=None) -> AddPowerSourceResponse`
- `rename_power_source(project_id, power_source_id, new_name) -> OperationResult`
- `delete_power_source(project_id, power_source_id) -> OperationResult`
- `set_power_source_value(project_id, power_source_id, power_w_per_m) -> OperationResult`
- `toggle_assign_power_source_object(project_id, power_source_id, object_name) -> OperationResult`
- `add_temperature(project_id, name=None) -> AddTemperatureResponse`
- `rename_temperature(project_id, temperature_id, new_name) -> OperationResult`
- `delete_temperature(project_id, temperature_id) -> OperationResult`
- `set_temperature_value(project_id, temperature_id, temperature_c) -> OperationResult`
- `toggle_assign_temperature_surface(project_id, temperature_id, surface_name) -> OperationResult`
- `get_boundary_config(project_id) -> BoundaryConfigResponse`
- `sync_project_state(project_id) -> SyncResult`

### Step 1-3 completion notes (2026-02-12)
- Added new files:
  - `integration/dto.py`
  - `integration/api.py`
  - `integration/local_adapter.py`
  - `integration/__init__.py`
- `app/ui/model_builder.py` BC mutation handlers now delegate through local adapter methods for:
  - add/delete/rename item
  - set numeric value
  - assign/unassign object/surface
  - remove selected assignment rows
- Added adapter-focused tests:
  - `tests/test_integration_dto.py`
  - `tests/test_integration_api_contract.py`
  - `tests/test_local_adapter.py`

### Policy decisions
- UI must call adapter methods for domain mutations (no direct trame-state mutation for BC business actions after migration).
- Local adapter is authoritative during development; backend sync is required before simulation commands.
- Simulation must run from a backend-acknowledged snapshot when remote backend is enabled.
- Local-only edits must mark project as dirty/unsynced.

### Out-of-scope for this milestone
- Rewriting all non-BC modules at once.
- Final transport protocol selection (REST/gRPC/message bus).
- Full persistence redesign.
  - Temperature assignment highlighting is **surface-only** (selected face), not whole-object highlight.
- **Global exclusivity rules**:
  - One object can belong to only one power source.
  - One surface can belong to only one temperature.
  - Conflict is rejected with log message (existing assignment kept).
- **Delete item support** retained for both categories with icon-only light-gray trash button.

**Implementation notes:**
- `engine/geometry.py` now returns deterministic CAD face entries per object (`Face-1..N`) from face traversal order.
- `viewer.py` renders per-face actors and resolves object/surface picks; fallback uses world-position nearest-centroid mapping for robust headless picks.
- `model_builder.py` owns assignment state/control logic:
  - active assignment context from expanded row
  - toggle add/remove
  - exclusivity checks
  - input value updates

**Screenshot Verification**

| User Action | Before | After | Screenshot |
|-------------|--------|-------|------------|
| Expand Power Source 1 row | Collapsed item | Assignment box + `+/-` + Power input visible | `bc_power_source_expanded.png` |
| Expand Temperature 1 row | Collapsed item | Assignment box + `+/-` + Temperature input visible | `bc_temperature_expanded.png` |
| Click row text (Power Source/Temperature) | Row collapsed | Row expands (same behavior as chevron click) | `bc_power_source_expanded.png`, `bc_temperature_expanded.png` |
| Click object while Power Source 1 expanded | No assignment | Object added; repeat click toggles off | `bc_power_source_assignment_exclusive.png` |
| Click surface while Temperature 1 expanded | No assignment | Surface label `Object:Face-N` added; repeat click toggles off; selected face is highlighted | `bc_temperature_surface_assignment_exclusive.png` |
| Try assigning same object/surface to second item | Already assigned to first | Rejected; second item list unchanged | `bc_power_source_assignment_exclusive.png`, `bc_temperature_surface_assignment_exclusive.png` |
| Select assigned row + click `-` | Row selected | Row removed from list; list remains fixed-height/scrollable | `bc_temperature_surface_assignment_exclusive.png` |

---

## Milestone 3: Build Sub-Model Pipeline — PENDING

## Milestone 4: Solving & Result Visualization — PENDING

## Milestone 5: Boundary Condition Parameters — PENDING

## Milestone 6: Project Persistence — PENDING
