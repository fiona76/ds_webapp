# DS WebApp UI Behavior Specification

## Purpose
- Define expected user-visible behavior for current UI features.
- Serve as the detailed behavior reference for development and regression verification.

## Link Entry and Project Start
- The app is intended to be accessed from a shared link.
- First-time users (no saved project yet) can create a new blank project and continue. They can save it later.
- Returning users can open a saved project to resume from their previous state.
- Once a new blank project is created, the standard layout and panel behavior below applies.

## User Workflow
1. **Open shared link** — user lands in project start prompt.
2. **Start project** — choose `Create New Project` (first-time path) or `Open Saved Project` (resume path).
3. **New project path** — creating a blank project opens the standard layout and panels.
4. **Geometry load** — add geometry from demo examples or local upload/import. Imports appear as `Import 1`, `Import 2`, ... in Geometry Settings.
5. **Object settings** — expand an import row; Settings shows object list with material assignment.
6. **Materials** — create blank materials or load default materials, then edit catalog/properties.
7. **Boundary Conditions** — click Boundary Condition to select physics type; then click Power Source, Temperature, Stress, or Time Step (depending on physics) to add and configure items.
8. **Modelization** — choose parameters for sub-model partitioning.
9. **Build Sub-Model** — FVM or AI model generation. Mesh is automatic.
10. **Solving** — click Run.
11. **Result** — select a simulation; VTU renders in viewport.
12. **Save project** — download a self-contained ZIP so the session can be resumed later.

## Layout and Panels
- Top menu has `File` (New, Open, Save, Save As) and `Edit` (Undo, Redo).
- Left side contains `Model Builder` and `Settings` (collapsible together). Both panels can be resized by dragging the dividers on either side of Settings.
- Center contains 3D viewport and toolbar.
- Bottom contains `Log` (collapsible independently).
- Settings is a context-sensitive panel — shows properties for whichever Model Builder item is selected.

## Viewport

### Toolbar
Four independent display mode toggles (any combination valid):

| Icon | Default | Behavior |
|------|---------|----------|
| `mdi-grid` | ON | Triangle mesh edge visibility on surfaces |
| `mdi-circle-half-full` | OFF | 40% opacity on surfaces. With selection: selected object stays 100%, others 40% |
| `mdi-cube-outline` | ON | CAD feature edge line actors (real BRep edges, not mesh wireframe) |
| `mdi-lightbulb-outline` | ON | ON = shaded (ambient 0.2, diffuse 0.8). OFF = flat (ambient 1.0, diffuse 0.0) |

Mesh edges (icon 1) and feature edges (icon 3) are different: icon 1 shows triangulation mesh on surfaces, icon 3 shows actual CAD boundary edges as separate line actors.

### Controls
- **Reset view button** at bottom-left of viewport. Resets camera to fit all geometry.

### Highlight and Selection Behavior
- Normal mode (no active BC assignment item):
  - Selected object is highlighted (orange). Click again to deselect.
- Active Power Source assignment mode:
  - All assigned objects for active item are highlighted.
  - Selecting rows in assignment list does not narrow highlight to a single row.
- Active Temperature assignment mode:
  - All assigned surfaces for active item are highlighted (surface-only, not whole-object).
  - Selecting rows in assignment list does not narrow highlight to a single row.
- When no BC assignment item is active, assignment highlight context is cleared.
- When switching from BC to Geometry, BC highlight must be fully cleared before any new geometry selection.

## Model Builder
- Top-level nodes:
  - Geometry
  - Boundary Condition
  - Materials
  - Modelization
  - Build Sub-Model
  - Solving
  - Result
- `Boundary Condition` expands to show physics-dependent leaf nodes.
  - The **physics type** is selected in the Boundary Condition Settings panel (when the BC node itself is selected).
  - The visible leaf nodes update immediately based on the chosen physics type:

| Physics type | Visible leaves |
|---|---|
| Static Thermal | Power Source, Temperature |
| Transient Thermal | Power Source, Temperature, Time Step |
| Static Stress | Stress |
| Transient Stress | Stress, Time Step |
| Static Thermal-Mechanical | Power Source, Temperature, Stress |
| Transient Thermal-Mechanical | Power Source, Temperature, Stress, Time Step |

- Changing physics type preserves all BC items — switching back restores them.
- BC items (`Power Source 1..N`, `Temperature 1..N`, `Stress 1..N`) are managed in Settings only — they do NOT appear as tree children.

## Geometry Sources and Import
- Geometry loading supports two user paths:
  - `Demo geometry` provided by the app (example models for quick start/demo).
  - `Local upload` from the user's machine (STEP/STP now, extensible to additional formats later).
- Current local-development flow may use the existing server-side file browser dialog:
  - Path bar at top with editable text field and up-arrow button for parent directory.
  - Directory listing shows folders (`mdi-folder`) and supported geometry files (`mdi-file-cad-box`). Sorted: directories first, then files. Hidden files excluded.
  - Click a folder to navigate into it. Click a file to select it (highlighted blue).
  - "Selected:" label at bottom shows full path. Import button disabled until a file is selected.
- On successful geometry load:
  - `Import N` appears as expandable row in Geometry Settings.
  - Geometry renders in viewport when the import row is expanded.
  - Settings shows source info and object list (e.g., PCB_OUTLINE, CHIP, 3DVC).

## Materials Workflow

### Tree structure
- `Materials` is a collapsible node in Model Builder (same pattern as Geometry and Boundary Condition).
- Expanding `Materials` reveals two action items:
  - `Create Blank Material` — immediately adds a new empty material to the project and switches Settings to the materials list.
  - `Add Material from Default` — immediately bulk-loads all default materials from the redrock library into the project, then switches Settings to the materials list.

### Settings: Materials (`active_node === 'materials'`)
- Shows the list of all project materials (blank and default-loaded).
- Each material is a collapsible row (name + chevron), same expand/collapse pattern as Power Source items.
- Status message shown below the list when an action succeeds or fails.

#### Inline rename
- Double-click a material name to edit it inline (same pattern as BC item rename).
- Enter or blur commits the new name.

#### Expanded property rows
Each property is shown as one or more labeled input rows. Property names have underscores replaced with spaces and the first letter capitalised (e.g. `thermal_conductivity` → `Thermal conductivity`).

- **Scalar property** — one row:
  ```
  Density :  [2320]  kg/m^3
  ```
- **Tensor property (orthotropic, 3 components)** — three rows:
  ```
  Thermal conductivity - x :  [131]  W/(m*K)
  Thermal conductivity - y :  [131]  W/(m*K)
  Thermal conductivity - z :  [131]  W/(m*K)
  ```
- **Dimensionless property** (e.g. `poissons_ratio`) — no units label shown.
- Values are editable number inputs; changes are committed on blur.
- Units are read-only labels.

### Add Material from Default behavior
- All default materials are loaded in one bulk API call.
- If a default material has the same name as an existing project material, it is silently skipped (existing is kept). The log panel records which names were skipped.
- Future: a conflict dialog will let users choose per-conflict whether to keep existing or replace.

### Create Blank Material behavior
- Adds a new material with a generated placeholder name (e.g. `Material 1`, `Material 2`, ...).
- All catalog properties are shown immediately as empty input rows, ready for the user to fill in.
- The material name can be changed via double-click inline rename.

### General behavior
- Users can have multiple materials in one project.
- Loaded default materials are copied into project scope; edits do not mutate the global default library.
- Materials are project-scoped and included in project save/load.

## Boundary Condition Settings

### Physics selector (always visible when Boundary Condition is expanded)
- A `Physics Type` dropdown is shown directly in the Model Builder tree, inside the Boundary Condition group.
- Options: Static Thermal, Transient Thermal, Static Stress, Transient Stress, Static Thermal-Mechanical, Transient Thermal-Mechanical.
- Default: **nothing selected** — no BC leaves are visible until a physics type is chosen.
- Changing physics type immediately updates the tree leaves visible below the dropdown.
- The dropdown is clearable; clearing it hides all BC leaves.

### Common (Power Source, Temperature, Stress)
- Rows are expandable by clicking row text or chevron.
- Expanded panel has fixed-height assignment list with smaller/tighter text and vertical scrolling.
- **Assignment mode dropdown** appears above the assignment list:
  - Power Source: `All Domains` or `Manual` (default: Manual)
  - Temperature / Stress: `All Boundaries` or `Manual` (default: Manual)
  - Selecting `All Domains` / `All Boundaries` auto-fills the list with every available object or surface from all imported geometry files.
  - Removing any item from an `All Domains`/`All Boundaries` list silently reverts the dropdown to `Manual`; remaining items stay.
- Assignment list supports:
  - single click
  - Ctrl/Cmd multi-select
  - Shift range select
- `-` removes all selected rows (from both active and overridden lists).
- `+` opens "not implemented" placeholder dialog.
- Double-click item name to inline rename. Enter or blur commits. All other items stay visible during editing.
- Delete button on each row removes that item.
- **Silent conflict (steal):** assigning an object/surface already owned by another BC item silently steals it. The previous owner shows it as greyed italic `CHIP (overridden)` in its list.
- **Reclaim:** clicking an `(overridden)` entry in a BC item's list immediately reclaims it — moves it back to that item and removes it from the current owner.

### Power Source
- Add button creates `Power Source N`.
- Expanded row shows:
  - `Power (W/m)` input, default `0`
  - `Assigned Objects` list
- Object assignment:
  - Clicking object in viewport toggles assignment.
  - Object can belong to only one power source globally (conflicting assignment rejected).

### Temperature
- Add button creates `Temperature N`.
- Expanded row shows:
  - `Temperature (oC)` input, default `0`
  - `Assigned Surfaces` list
- Surface assignment:
  - Clicking CAD face in viewport toggles assignment.
  - Label format: `ObjectName:Face-N`.
  - Surface can belong to only one temperature globally (conflicting assignment rejected).

### Stress
- Add button creates `Stress N`.
- Expanded row shows:
  - `Pressure / Force (Pa)` input, default `0`
  - `Assigned Surfaces` list
- Surface assignment:
  - Clicking CAD face in viewport toggles assignment (same interaction as Temperature).
  - Label format: `ObjectName:Face-N`.
  - Surface can belong to only one stress BC globally (conflicting assignment rejected).

### Time Step
- Singleton section — no list, no add/delete.
- Shows two input fields:
  - `Duration (s)` — total simulation duration
  - `Resolution (s)` — time step size
- Values are committed on blur.

## Undo / Redo

### Scope
Undo and redo track **model-definition edits** only. Execute-phase operations (Modelization, Build Sub-Model, Solving) are excluded — they fire backend computation and have no meaningful UI inverse.

Tracked operations (all undoable):
| Area | Operations |
|------|-----------|
| Geometry | Import STEP file |
| Materials | Create blank material, load default materials, rename material, edit property value |
| Boundary Condition | Add / delete Power Source, Temperature, or Stress; rename, set value, assign/unassign objects or surfaces |

### Behavior
- **Undo** restores the state to immediately before the last tracked action.
- **Redo** re-applies an undone action.
- History depth: **50 steps**. Older entries are dropped when the limit is exceeded.
- Performing any new edit after an undo clears the redo stack (standard linear history).
- Running Modelization, Build Sub-Model, or Solving does **not** clear undo history — users can still undo model edits made before a simulation run.

### Triggering undo/redo
| Method | Undo | Redo |
|--------|------|------|
| Keyboard | `Ctrl+Z` | `Ctrl+Y` or `Ctrl+Shift+Z` |
| Edit menu | Edit → Undo | Edit → Redo |

- Keyboard shortcuts are suppressed when focus is inside a text input (to preserve browser-native text-edit undo).
- Edit menu items show the keyboard hint as a subtitle and are greyed out when no history is available.

## Project Save and Resume

### Overview
- The app is stateless on the server — no user accounts, no server-side storage per user.
- Each user's project data is owned by the user as a downloadable file on their machine.
- Multiple users can share the same app link without seeing each other's work.

### File format
- Projects are saved as a **ZIP file** containing:
  - `project.json` — all project metadata, materials, BC definitions, netlist, geom, and simulation results.
  - The original STEP geometry file(s) embedded by content (not by path), so the project is fully self-contained and portable across machines.

### Saved content
- Geometry file(s) (embedded STEP bytes, not file path references).
- Materials JSON (current material definitions).
- Boundary condition data (physics type, all BC items with assignments).
- Netlist data.
- Geometry processing data (`geom`).
- Simulation result artifact (`VTM`) when available.

### Save behavior (File → Save)
- If the project was previously saved or opened from a file: re-downloads a ZIP with the **same suggested filename**.
- If the project has never been saved (new blank project): falls through to Save As behavior.
- The browser's native "Save As" OS dialog appears; the user chooses where to store the file.

### Save As behavior (File → Save As)
- Always prompts for a new filename via the browser download dialog.
- Downloads a new ZIP regardless of whether the project was previously saved.

### Open behavior (File → Open)
- Shows a file picker; user selects a previously saved ZIP from their machine.
- Server unpacks the ZIP, restores all project state, and re-renders geometry in the viewport.
- Project is immediately considered **clean** (no unsaved changes) after a successful open.

### Dirty state and unsaved-changes warning
- The project becomes **dirty** (has unsaved changes) after any undo-tracked operation since the last save or open.
- When the user attempts to close or navigate away from the browser tab with a dirty project, the browser shows a native "Leave site? Changes you made may not be saved." warning dialog.
- The warning is suppressed when the project is clean (just saved or just opened).
- Executing Modelization, Build Sub-Model, or Solving marks the project dirty (computed artifacts changed).

### Resume behavior
- Opening a saved ZIP restores the full workflow state — geometry, materials, BC, and results — exactly as left.
- Users can continue from where they left off without re-running any steps, as all computed data is included in the file.

## Verification Mapping
- Automated behavior checks are maintained in `tests/` (Playwright + adapter tests).
- See `verification.md` for how to run tests and where to add new ones.
