# Learning Notes

## Learning 1: VtkLocalView Delta Serializer Cache Aliasing

### The Bug

After the sequence **Import STEP -> highlight CHIP -> BC Power Source -> assign objects -> back to Geometry -> highlight CHIP**, the viewport failed to show the orange highlight. State was correct (`selected_object = "CHIP"`), but the visual didn't update.

### Root Cause

`VtkLocalView` renders client-side in vtk.js. Every `view.update()` call runs a **delta serializer** that compares current VTK actor properties against a global `PROP_CACHE` (in `trame_vtk/modules/vtk/serializers/cache.py`). It only sends properties that changed since last update.

The cache keys are **C++ memory addresses** extracted by `reference_id()` (using `ref.__this__[1:17]`), not Python object `id()`.

When `show_geometry()` destroyed old actors and created new ones for the **same geometry data**:

1. `renderer.RemoveActor(old_actor)` freed the C++ object
2. `vtkActor()` allocated a new C++ object at the **same memory address** (C++ allocator reuse)
3. `PROP_CACHE` still had the old entry for that address with the old property values
4. Delta serializer compared new properties against stale cache, concluded "nothing changed", sent an empty delta
5. Client never received the property update, so actors stayed the wrong color

### The Fix

Added a `_displayed_objects_id` tracker in `viewer.py` that uses Python's `id()` on the geometry object list to detect when the same data is already displayed:

```python
_displayed_objects_id = [None]

def show_geometry(objects):
    obj_id = id(objects) if objects else None
    if obj_id is not None and obj_id == _displayed_objects_id[0] and current_actors:
        # Same geometry already shown -- just restyle, don't rebuild actors
        _apply_all_styles()
        return
    _displayed_objects_id[0] = obj_id
    # ... full teardown + rebuild ...
```

This works because `_geometry_meshes[import_id]` always returns the **same Python list reference** for the same import. Navigating away and back passes the same list, so `id()` matches, the actor rebuild is skipped, and `_apply_all_styles()` updates properties on the existing (still-alive) actors. The delta serializer then sees real property changes and sends them correctly.

### Approaches That Did NOT Work

| Approach | Result |
|----------|--------|
| Pop stale `PROP_CACHE` entries before destroying actors | Geometry disappeared entirely -- broke the serializer's expectations |
| `render_window.Modified()` before `view_update()` | No effect -- mtime change didn't force client reprocessing |
| Custom full-state-only update (skip delta, only `new_state=True`) | Broke initial highlight -- publishing full state as delta confuses vtk.js |
| Push empty scene between teardown and rebuild | Still didn't fix it -- new actors still aliased old cache entries |

### Principles for Future Geometry Views

As the app grows (Modelization, Results, etc.), new panels will need to show different geometry in the viewport. Follow these rules:

**1. Store mesh data as a persistent reference -- don't recreate lists unnecessarily.**

```python
# GOOD -- same list object persists, id() stays stable
_geometry_meshes[import_id] = result["objects"]
# Later calls pass the same reference:
show_geometry(_geometry_meshes[import_id])

# BAD -- creates a new list each time, defeats the id() guard
show_geometry(list(_geometry_meshes[import_id]))
show_geometry([obj for obj in _geometry_meshes[import_id]])
```

**2. Different data sources should be different Python objects.**

When switching between truly different geometry (Import 1 vs Import 2, STEP mesh vs VTU result), the lists will naturally have different `id()` values, so `show_geometry()` will do a full rebuild. This is correct -- new data needs new actors.

```python
_modelization_meshes = {}   # separate dict for modelization data
_result_meshes = {}         # separate dict for result VTU data

# Switching from geometry to results:
show_geometry(_result_meshes[result_id])
# id(result list) != id(geometry list) --> full rebuild, correct
```

**3. Never destroy and recreate actors for the same data.**

The serializer aliasing bug only triggers when actors are torn down and rebuilt with equivalent data. If you must rebuild (e.g., mesh data actually changed), consider one of:
- Replace the list in the data store so the `id()` changes naturally
- Set `_displayed_objects_id[0] = None` before calling `show_geometry()` to force a rebuild

```python
# Data actually changed -- replace the reference so id() changes
_geometry_meshes[import_id] = new_result["objects"]  # new list object
show_geometry(_geometry_meshes[import_id])            # id() won't match, full rebuild
```

**4. All restyling (highlight, display modes) goes through `_apply_all_styles()`.**

Never call `view_update()` directly for style changes. `_apply_all_styles()` updates all actor properties in one pass and calls `view_update()` exactly once. Multiple rapid `view_update()` calls can also cause serializer issues.

**5. Use `_batch_updating` guard for multi-state changes.**

When changing multiple state keys (e.g., clearing `selected_object` + `selected_surface` + `bc_active_assignment_id`), set `_batch_updating = True` to suppress intermediate `_apply_all_styles()` calls from state watchers, then do a single `_apply_all_styles()` or `show_geometry()` at the end.

### Quick Reference: When Does What Happen?

| Scenario | `id()` match? | Action |
|----------|--------------|--------|
| Navigate away and back to same import | Yes | Skip rebuild, restyle only |
| Switch from Import 1 to Import 2 | No | Full rebuild (correct) |
| Switch from Geometry to Results | No | Full rebuild (correct) |
| Re-import same STEP file (new parse) | No | Full rebuild (new list from parser) |
| Toggle display mode (edges, transparency) | N/A | `_apply_all_styles()` only, no `show_geometry()` |
| Click to highlight an object | N/A | `_apply_all_styles()` only, no `show_geometry()` |
