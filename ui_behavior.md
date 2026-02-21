# DS WebApp UI Behavior Specification

## Purpose
- Define expected user-visible behavior for current UI features.
- Serve as the detailed behavior reference for development and regression verification.

## Link Entry and Project Start
- The app is intended to be accessed from a shared link.
- First-time users (no saved project yet) can create a new blank project and continue. They can save it later.
- Returning users can open a saved project to resume from their previous state.
- Once a new blank project is created, the standard layout and panel behavior below applies.

## Layout and Panels
- Top menu has `File` (New, Open, Save, Save As) and `Edit` (Undo, Redo).
- Left side contains `Model Builder` and `Settings` (collapsible together). Both panels can be resized by dragging the dividers on either side of Settings.
- Center contains 3D viewport and toolbar.
- Bottom contains `Log` (collapsible independently).
- Settings is a context-sensitive panel — shows properties for whichever Model Builder item is selected.

## Undo / Redo

### Scope
Undo and redo track **model-definition edits** only. Execute-phase operations (Modelization, Build Sub-Model, Solving) are excluded — they fire backend computation and have no meaningful UI inverse.

Tracked operations (all undoable):
| Area | Operations |
|------|-----------|
| Geometry | Import STEP file |
| Materials | Create blank material, load default materials, rename material, edit property value |
| Boundary Condition | Add / delete Power Source or Temperature, rename, set value, assign/unassign objects or surfaces |

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

## Model Builder
- Top-level nodes:
  - Geometry
  - Boundary Condition
  - Materials
  - Modelization
  - Build Sub-Model
  - Solving
  - Result
- `Boundary Condition` expands to show only:
  - `Power Source`
  - `Temperature`
- BC items (`Power Source 1..N`, `Temperature 1..N`) are managed in Settings only — they do NOT appear as tree children.

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

### Common
- Rows are expandable by clicking row text or chevron.
- Expanded panel has fixed-height assignment list with smaller/tighter text and vertical scrolling.
- Assignment list supports:
  - single click
  - Ctrl/Cmd multi-select
  - Shift range select
- `-` removes all selected rows.
- `+` opens "not implemented" placeholder dialog.
- Double-click item name to inline rename. Enter or blur commits. All other items stay visible during editing.
- Delete button on each row removes that item.

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

## Highlight and Selection Behavior
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


## Project Save and Resume
- Project save persists enough information to restore the same progress later.
- Saved content includes:
  - Geometry source references (path to local geometry or pointer to demo geometry).
  - Materials JSON (current material definitions from Materials workflow).
  - Netlist data.
  - Geometry processing data (`geom`).
  - Boundary condition data (`BC`).
  - Simulation result artifact (`VTM`) when available.
- Opening a saved project restores the same workflow state so users can continue where they left off.


## Viewport Toolbar

Four independent display mode toggles (any combination valid):

| Icon | Default | Behavior |
|------|---------|----------|
| `mdi-grid` | ON | Triangle mesh edge visibility on surfaces |
| `mdi-circle-half-full` | OFF | 40% opacity on surfaces. With selection: selected object stays 100%, others 40% |
| `mdi-cube-outline` | ON | CAD feature edge line actors (real BRep edges, not mesh wireframe) |
| `mdi-lightbulb-outline` | ON | ON = shaded (ambient 0.2, diffuse 0.8). OFF = flat (ambient 1.0, diffuse 0.0) |

Mesh edges (icon 1) and feature edges (icon 3) are different: icon 1 shows triangulation mesh on surfaces, icon 3 shows actual CAD boundary edges as separate line actors.

## Viewport Controls
- **Reset view button** ok,at bottom-left of viewport. Resets camera to fit all geometry.

## User Workflow
1. **Open shared link** — user lands in project start prompt.
2. **Start project** — choose `Create New Project` (first-time path) or `Open Saved Project` (resume path).
3. **New project path** — creating a blank project opens the standard layout and panels.
4. **Geometry load** — add geometry from demo examples or local upload/import. Imports appear as `Import 1`, `Import 2`, ... in Geometry Settings.
5. **Object settings** — expand an import row; Settings shows object list with material assignment.
6. **Materials** — create blank materials or load default materials, then edit catalog/properties.
7. **Boundary Conditions** — click Power Source or Temperature, add items, assign objects/surfaces via viewport.
8. **Modelization** — choose parameters for sub-model partitioning.
9. **Build Sub-Model** — FVM or AI model generation. Mesh is automatic.
10. **Solving** — click Run.
11. **Result** — select a simulation; VTU renders in viewport.
12. **Save project** — persist geometry references, materials JSON, netlist, geom, BC, and VTM so reopening restores the same progress.

## Verification Mapping
- Automated behavior checks are maintained in `tests/` (Playwright + adapter tests).
- See `verification.md` for how to run tests and where to add new ones.
