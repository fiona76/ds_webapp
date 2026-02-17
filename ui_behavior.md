# DS WebApp UI Behavior Specification

## Purpose
- Define expected user-visible behavior for current UI features.
- Serve as the detailed behavior reference for development and regression verification.

## Layout and Panels
- Top menu has `File` (New, Open, Save, Save As) and `Edit` (Undo, Redo, Select All, Clear Selection).
- Left side contains `Model Builder` and `Settings` (collapsible together).
- Center contains 3D viewport and toolbar.
- Bottom contains `Log` (collapsible independently).
- Settings is a context-sensitive panel — shows properties for whichever Model Builder item is selected.

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

## Geometry Import
- Import uses a server-side file browser dialog (not a simple text field):
  - Path bar at top with editable text field and up-arrow button for parent directory.
  - Directory listing shows folders (`mdi-folder`) and `.step`/`.stp` files (`mdi-file-cad-box`). Sorted: directories first, then files. Hidden files excluded.
  - Click a folder to navigate into it. Click a file to select it (highlighted blue).
  - "Selected:" label at bottom shows full path. Import button disabled until a file is selected.
- On successful import:
  - `Import N` appears as expandable row in Geometry Settings.
  - Geometry renders in viewport when the import row is expanded.
  - Settings shows file info and object list (e.g., PCB_OUTLINE, CHIP, 3DVC).

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

## Viewport Toolbar

Four independent display mode toggles (any combination valid):

| Icon | State Key | Default | Behavior |
|------|-----------|---------|----------|
| `mdi-grid` | `viewer_show_edges` | ON | Triangle mesh edge visibility on surfaces |
| `mdi-circle-half-full` | `viewer_semi_transparent` | OFF | 40% opacity on surfaces. With selection: selected object stays 100%, others 40% |
| `mdi-cube-outline` | `viewer_wireframe` | ON | CAD feature edge line actors (real BRep edges, not mesh wireframe) |
| `mdi-lightbulb-outline` | `viewer_scene_light` | ON | ON = shaded (ambient 0.2, diffuse 0.8). OFF = flat (ambient 1.0, diffuse 0.0) |

Mesh edges (icon 1) and feature edges (icon 3) are different: icon 1 shows triangulation mesh on surfaces, icon 3 shows actual CAD boundary edges as separate line actors.

## Viewport Controls
- **Reset view button** (`mdi-fit-to-screen-outline`) at bottom-left of viewport. Resets camera to fit all geometry.

## User Workflow
1. **File > New** — start a new project.
2. **Geometry import** — import 1..N STEP files. Each appears as `Import 1`, `Import 2`, … in Geometry Settings.
3. **Object settings** — expand an import row; Settings shows object list with material assignment.
4. **Materials** — adjust per-material thermal conductivity (kx/ky/kz). JSON import for bulk properties.
5. **Boundary Conditions** — click Power Source or Temperature, add items, assign objects/surfaces via viewport.
6. **Modelization** — choose parameters for sub-model partitioning.
7. **Build Sub-Model** — FVM or AI model generation. Mesh is automatic.
8. **Solving** — click Run.
9. **Result** — select a simulation; VTU renders in viewport.

## Verification Mapping
- Automated behavior checks are maintained in `tests/` (Playwright + adapter tests).
- See `verification.md` for how to run tests and where to add new ones.
