from trame.widgets import vuetify3 as v3, html as html_widgets

from app.engine.geometry import import_step_file
from app.history import UndoHistory
from integration.factory import create_integration_adapter

# Module-level singleton — history survives across trame state resets.
_history = UndoHistory()

# Top-level tree nodes (static)
MODEL_BUILDER_NODES = [
    {"id": "geometry", "title": "Geometry", "icon": "mdi-cube-outline"},
    {"id": "boundary_condition", "title": "Boundary Condition", "icon": "mdi-border-outside"},
    {"id": "materials", "title": "Materials", "icon": "mdi-atom"},
    {"id": "modelization", "title": "Modelization", "icon": "mdi-grid"},
    {"id": "build_sub_model", "title": "Build Sub-Model", "icon": "mdi-hammer-wrench"},
    {"id": "solving", "title": "Solving", "icon": "mdi-play-circle"},
    {"id": "result", "title": "Result", "icon": "mdi-chart-line"},
]


def create_model_builder(server):
    state = server.state
    state.active_node = None
    state.selected_object = None  # currently highlighted object name in viewport
    state.selected_surface = None  # currently highlighted surface label (Object:Face-N)
    # List of imported geometry files: [{id, file_name, file_path, objects (names only)}]
    state.geometry_imports = []
    state.geometry_import_counter = 0
    state.viewer_geometry_unit = "mm"
    state.geo_unit_options = ["mm", "m", "cm", "um", "nm"]
    # Controls the file input dialog trigger
    state.trigger_file_input = 0
    # Which import row is currently expanded in Settings (empty = none)
    state.geometry_expanded_import_id = ""

    # Boundary Condition items
    state.bc_power_sources = []       # [{id: "ps_1", name: "Power Source 1"}, ...]
    state.bc_temperatures = []        # [{id: "temp_1", name: "Temperature 1"}, ...]
    state.bc_power_source_counter = 0
    state.bc_temperature_counter = 0
    state.bc_expanded_power_source_id = ""
    state.bc_expanded_temperature_id = ""
    state.bc_active_assignment_type = ""   # "power_source" | "temperature" | ""
    state.bc_active_assignment_id = ""     # ps_* | temp_* | ""
    state.bc_selected_assignment_item_id = ""
    state.bc_selected_assignment_values = []
    state.bc_selection_anchor_index = -1
    state.show_bc_add_placeholder = False
    state.bc_add_placeholder_message = ""
    state.materials_catalog = []
    state.materials_items = []
    state.materials_expanded_item = ""
    state.materials_editing_id = ""
    state.materials_editing_name = ""
    state.materials_counter = 0
    state.materials_last_result = ""
    state.undo_available = False
    state.redo_available = False

    # Server-side storage for mesh data (not in trame state — too large)
    _geometry_meshes = {}  # import_id -> list of object dicts with vertices/triangles

    # Integration adapter — all BC business logic delegates here
    _adapter = create_integration_adapter(state)
    _PROJECT_ID = "default"

    # Guard flag: when True, suppress automatic highlight_object() calls
    # from state-change watchers to avoid multiple rapid view_update() calls.
    # Used in on_node_change AND toggle_geometry_import_expanded.
    _batch_updating = False

    def _log(msg):
        state.log_messages = state.log_messages + [msg]

    def _push():
        """Snapshot state onto the undo stack before a guaranteed mutation."""
        _history.push(state)

    @state.change("active_node")
    def on_node_change(active_node, **_):
        nonlocal _batch_updating
        if not active_node:
            return
        _batch_updating = True
        _log(f"[Model Builder] Selected: {active_node}")
        # Clear selection and BC state BEFORE showing geometry, so that
        # show_geometry → _apply_all_styles reads the already-cleared state.
        state.selected_object = None
        state.selected_surface = None
        if active_node not in ("bc_power_source", "bc_temperature"):
            state.bc_expanded_power_source_id = ""
            state.bc_expanded_temperature_id = ""
            state.bc_active_assignment_type = ""
            state.bc_active_assignment_id = ""
            state.bc_selected_assignment_item_id = ""
            state.bc_selected_assignment_values = []
            state.bc_selection_anchor_index = -1
        # Clear geometry expanded state when leaving geometry
        if active_node != "geometry":
            state.geometry_expanded_import_id = ""
        # Show geometry if an import is currently expanded under geometry
        if active_node == "geometry" and state.geometry_expanded_import_id in _geometry_meshes:
            if hasattr(server.controller, "show_geometry"):
                server.controller.show_geometry(_geometry_meshes[state.geometry_expanded_import_id])
        else:
            # No geometry rebuild, but still need to push style changes
            if hasattr(server.controller, "highlight_object"):
                server.controller.highlight_object()
        _batch_updating = False

    @state.change("selected_object", "selected_surface")
    def on_object_selected(**_):
        if _batch_updating:
            return  # suppress during batch updates to avoid redundant view_update()
        if hasattr(server.controller, "highlight_object"):
            server.controller.highlight_object()

    def on_step_file_imported(file_path):
        """Called when a STEP file is selected via the server-side file input."""
        try:
            result = import_step_file(file_path)
            _push()  # capture before state changes; parse already succeeded
            state.geometry_import_counter = state.geometry_import_counter + 1
            import_id = f"import_{state.geometry_import_counter}"

            # Store mesh data server-side
            _geometry_meshes[import_id] = result["objects"]

            # Store only names in trame state for UI
            object_names = [obj["name"] for obj in result["objects"]]
            import_entry = {
                "id": import_id,
                "label": f"Import {state.geometry_import_counter}",
                "file_name": result["file_name"],
                "file_path": result["file_path"],
                "objects": object_names,
                "unit": result["unit"],
            }
            state.geometry_imports = state.geometry_imports + [import_entry]
            state.viewer_geometry_unit = result["unit"]
            # Auto-expand the new import and navigate to geometry
            state.geometry_expanded_import_id = import_id
            state.active_node = "geometry"
            # Show geometry in viewport
            if hasattr(server.controller, "show_geometry"):
                server.controller.show_geometry(result["objects"])

            _log(f"[Geometry] Imported {result['file_name']} — {len(object_names)} objects: {', '.join(object_names)}")
        except Exception as e:
            _log(f"[Geometry] Error importing file: {e}")

    # Register the import handler on the controller so UI can call it
    server.controller.on_step_file_imported = on_step_file_imported

    def toggle_geometry_import_expanded(import_id):
        """Expand/collapse an import row in Settings. Shows geometry when expanded."""
        nonlocal _batch_updating
        _batch_updating = True
        if state.geometry_expanded_import_id == import_id:
            # Collapse — clear geometry from viewport
            state.geometry_expanded_import_id = ""
            state.selected_object = None
            state.selected_surface = None
            _batch_updating = False
            if hasattr(server.controller, "highlight_object"):
                server.controller.highlight_object()
        else:
            # Expand — show this import's geometry
            state.geometry_expanded_import_id = import_id
            state.selected_object = None
            state.selected_surface = None
            if import_id in _geometry_meshes:
                if hasattr(server.controller, "show_geometry"):
                    server.controller.show_geometry(_geometry_meshes[import_id])
            _batch_updating = False

    def add_power_source():
        snap = _history.capture(state)
        response = _adapter.add_power_source(_PROJECT_ID)
        if response.result.ok:
            _history.commit(snap, state)
            _log(f"[BC] Added {response.item['name']}")
        else:
            _log(f"[BC] Error adding power source: {response.result.message}")

    def add_temperature():
        snap = _history.capture(state)
        response = _adapter.add_temperature(_PROJECT_ID)
        if response.result.ok:
            _history.commit(snap, state)
            _log(f"[BC] Added {response.item['name']}")
        else:
            _log(f"[BC] Error adding temperature: {response.result.message}")

    def _ensure_catalog_loaded():
        if state.materials_catalog:
            return
        response = _adapter.get_materials_catalog()
        if response.result.ok:
            state.materials_catalog = [
                {"name": p.name, "kind": p.kind, "default_units": p.default_units, "symmetry": p.symmetry}
                for p in response.properties
            ]

    def create_blank_material():
        _ensure_catalog_loaded()
        _push()
        state.materials_counter = (state.materials_counter or 0) + 1
        name = f"Material {state.materials_counter}"
        # Pre-populate all catalog properties as empty constant slots
        properties = {}
        for prop in (state.materials_catalog or []):
            if prop["kind"] == "tensor" and prop.get("symmetry") == "orthotropic":
                properties[prop["name"]] = {"type": "constant", "value": [None, None, None], "units": prop["default_units"]}
            else:
                properties[prop["name"]] = {"type": "constant", "value": None, "units": prop["default_units"]}
        state.materials_items = (state.materials_items or []) + [
            {"name": name, "properties": properties}
        ]
        state.active_node = "materials"
        state.materials_last_result = f"Created '{name}'"
        _log(f"[Materials] Created blank material '{name}'")

    def load_all_default_materials():
        _ensure_catalog_loaded()
        response = _adapter.list_default_materials_full()
        if not response.result.ok:
            state.materials_last_result = response.result.message
            _log(f"[Materials] {response.result.message}")
            return
        _push()
        existing_names = {m["name"] for m in (state.materials_items or [])}
        added, skipped = [], []
        for mat in response.materials:
            if mat["name"] in existing_names:
                skipped.append(mat["name"])
            else:
                added.append({"name": mat["name"], "properties": mat["properties"]})
                existing_names.add(mat["name"])
        state.materials_items = (state.materials_items or []) + added
        state.active_node = "materials"
        msg = f"Loaded {len(added)} default material(s)"
        if skipped:
            msg += f"; skipped {len(skipped)} conflict(s): {', '.join(skipped)}"
        state.materials_last_result = msg
        _log(f"[Materials] {msg}")

    def toggle_material_expanded(name):
        state.materials_expanded_item = "" if state.materials_expanded_item == name else name

    def start_material_rename(name):
        state.materials_editing_id = name
        state.materials_editing_name = name

    def finish_material_rename(new_name):
        old_name = state.materials_editing_id
        new_name = (new_name or "").strip()
        state.materials_editing_id = ""
        state.materials_editing_name = ""
        if not new_name or new_name == old_name:
            return
        existing_names = [m["name"] for m in (state.materials_items or [])]
        if new_name in existing_names:
            state.materials_last_result = f"A material named '{new_name}' already exists"
            return
        _push()
        state.materials_items = [
            {**m, "name": new_name} if m["name"] == old_name else m
            for m in (state.materials_items or [])
        ]
        if state.materials_expanded_item == old_name:
            state.materials_expanded_item = new_name
        _log(f"[Materials] Renamed '{old_name}' to '{new_name}'")

    def set_material_property_value(mat_name, prop_name, component_index, raw_value):
        """Update one scalar value or one tensor component (component_index -1 = scalar)."""
        try:
            value = float(raw_value) if raw_value not in (None, "", "null") else None
        except (ValueError, TypeError):
            return
        _push()
        updated_items = []
        for mat in (state.materials_items or []):
            if mat["name"] != mat_name:
                updated_items.append(mat)
                continue
            props = {**mat["properties"]}
            prop = {**props.get(prop_name, {"type": "constant", "units": ""})}
            if component_index == -1:
                prop["value"] = value
            else:
                current = list(prop.get("value") or [None, None, None])
                current[component_index] = value
                prop["value"] = current
            props[prop_name] = prop
            updated_items.append({**mat, "properties": props})
        state.materials_items = updated_items

    def _clear_assignment_focus():
        state.bc_active_assignment_type = ""
        state.bc_active_assignment_id = ""
        state.bc_selected_assignment_item_id = ""
        state.bc_selected_assignment_values = []
        state.bc_selection_anchor_index = -1
        state.selected_object = None
        state.selected_surface = None
        if hasattr(server.controller, "highlight_object"):
            server.controller.highlight_object()

    def toggle_bc_item_expanded(item_id):
        if item_id.startswith("ps_"):
            if state.bc_expanded_power_source_id == item_id:
                state.bc_expanded_power_source_id = ""
                _clear_assignment_focus()
            else:
                state.bc_expanded_power_source_id = item_id
                state.bc_active_assignment_type = "power_source"
                state.bc_active_assignment_id = item_id
                state.bc_selected_assignment_item_id = ""
                state.bc_selected_assignment_values = []
                state.bc_selection_anchor_index = -1
                state.selected_object = None
                state.selected_surface = None
                if hasattr(server.controller, "highlight_object"):
                    server.controller.highlight_object()
        elif item_id.startswith("temp_"):
            if state.bc_expanded_temperature_id == item_id:
                state.bc_expanded_temperature_id = ""
                _clear_assignment_focus()
            else:
                state.bc_expanded_temperature_id = item_id
                state.bc_active_assignment_type = "temperature"
                state.bc_active_assignment_id = item_id
                state.bc_selected_assignment_item_id = ""
                state.bc_selected_assignment_values = []
                state.bc_selection_anchor_index = -1
                state.selected_object = None
                state.selected_surface = None
                if hasattr(server.controller, "highlight_object"):
                    server.controller.highlight_object()

    def _get_assignment_values(item_id):
        if item_id.startswith("ps_"):
            for it in state.bc_power_sources:
                if it["id"] == item_id:
                    return list(it.get("assigned_objects", []))
        elif item_id.startswith("temp_"):
            for it in state.bc_temperatures:
                if it["id"] == item_id:
                    return list(it.get("assigned_surfaces", []))
        return []

    def select_bc_assignment(item_id, value, index, shift_key=False, toggle_key=False):
        try:
            idx = int(index)
        except Exception:
            idx = 0

        values = _get_assignment_values(item_id)
        if not values or value not in values:
            state.bc_selected_assignment_item_id = item_id
            state.bc_selected_assignment_values = []
            state.bc_selection_anchor_index = -1
            return

        if state.bc_selected_assignment_item_id != item_id:
            state.bc_selected_assignment_item_id = item_id
            state.bc_selected_assignment_values = []
            state.bc_selection_anchor_index = -1

        selected = list(state.bc_selected_assignment_values)
        anchor = state.bc_selection_anchor_index

        if shift_key and anchor >= 0:
            lo = max(0, min(anchor, idx))
            hi = min(len(values) - 1, max(anchor, idx))
            selected = values[lo:hi + 1]
        elif toggle_key:
            if value in selected:
                selected = [v for v in selected if v != value]
            else:
                selected = selected + [value]
            anchor = idx
        else:
            selected = [value]
            anchor = idx

        # Preserve item order in selected list
        selected_set = set(selected)
        selected_ordered = [v for v in values if v in selected_set]
        state.bc_selected_assignment_item_id = item_id
        state.bc_selected_assignment_values = selected_ordered
        state.bc_selection_anchor_index = anchor

    def remove_selected_bc_assignment(item_id):
        if state.bc_selected_assignment_item_id != item_id:
            return
        selected_values = list(state.bc_selected_assignment_values)
        if not selected_values:
            return

        snap = _history.capture(state)
        result = _adapter.remove_selected_assignment(_PROJECT_ID, item_id, selected_values)
        if result.ok:
            _history.commit(snap, state)
            state.bc_selected_assignment_item_id = ""
            state.bc_selected_assignment_values = []
            state.bc_selection_anchor_index = -1
            if hasattr(server.controller, "highlight_object"):
                server.controller.highlight_object()

    def open_bc_add_placeholder(item_id):
        if item_id.startswith("ps_"):
            state.bc_add_placeholder_message = (
                "Custom object assignment flow is not implemented yet."
            )
        elif item_id.startswith("temp_"):
            state.bc_add_placeholder_message = (
                "Custom surface assignment flow is not implemented yet."
            )
        else:
            state.bc_add_placeholder_message = "Custom assignment flow is not implemented yet."
        state.show_bc_add_placeholder = True

    def set_bc_item_value(item_id, field_name, value):
        if item_id.startswith("ps_") and field_name == "power":
            snap = _history.capture(state)
            result = _adapter.set_power_source_value(_PROJECT_ID, item_id, value)
        elif item_id.startswith("temp_") and field_name == "temperature":
            snap = _history.capture(state)
            result = _adapter.set_temperature_value(_PROJECT_ID, item_id, value)
        else:
            return
        if result.ok:
            _history.commit(snap, state)
        else:
            _log(f"[BC] Error setting value: {result.message}")

    def toggle_assign_power_source_object(item_id, object_name):
        if not item_id or not object_name:
            return
        snap = _history.capture(state)
        result = _adapter.toggle_assign_power_source_object(_PROJECT_ID, item_id, object_name)
        if result.ok:
            _history.commit(snap, state)
            if result.message == "Unassigned":
                if state.bc_selected_assignment_item_id == item_id:
                    state.bc_selected_assignment_values = [
                        v for v in state.bc_selected_assignment_values if v != object_name
                    ]
                    if not state.bc_selected_assignment_values:
                        state.bc_selected_assignment_item_id = ""
                        state.bc_selection_anchor_index = -1
                _log(f"[BC] Unassigned object {object_name}")
            else:
                _log(f"[BC] Assigned object {object_name}")
            if hasattr(server.controller, "highlight_object"):
                server.controller.highlight_object()
        else:
            _log(f"[BC] {result.message}")

    def toggle_assign_temperature_surface(item_id, surface_name):
        if not item_id or not surface_name:
            return
        snap = _history.capture(state)
        result = _adapter.toggle_assign_temperature_surface(_PROJECT_ID, item_id, surface_name)
        if result.ok:
            _history.commit(snap, state)
            if result.message == "Unassigned":
                if state.bc_selected_assignment_item_id == item_id:
                    state.bc_selected_assignment_values = [
                        v for v in state.bc_selected_assignment_values if v != surface_name
                    ]
                    if not state.bc_selected_assignment_values:
                        state.bc_selected_assignment_item_id = ""
                        state.bc_selection_anchor_index = -1
                _log(f"[BC] Unassigned surface {surface_name}")
            else:
                _log(f"[BC] Assigned surface {surface_name}")
            if hasattr(server.controller, "highlight_object"):
                server.controller.highlight_object()
        else:
            _log(f"[BC] {result.message}")

    def rename_bc_item(item_id, new_name):
        if not new_name or not new_name.strip():
            return
        snap = _history.capture(state)
        if item_id.startswith("ps_"):
            result = _adapter.rename_power_source(_PROJECT_ID, item_id, new_name)
        elif item_id.startswith("temp_"):
            result = _adapter.rename_temperature(_PROJECT_ID, item_id, new_name)
        else:
            return
        if result.ok:
            _history.commit(snap, state)
        else:
            _log(f"[BC] Rename error: {result.message}")

    def delete_bc_item(item_id):
        """Delete a boundary-condition item by ID."""
        snap = _history.capture(state)
        if item_id.startswith("ps_"):
            result = _adapter.delete_power_source(_PROJECT_ID, item_id)
        elif item_id.startswith("temp_"):
            result = _adapter.delete_temperature(_PROJECT_ID, item_id)
        else:
            return

        if result.ok:
            _history.commit(snap, state)
            _log(f"[BC] Deleted {item_id}")
            if item_id.startswith("ps_") and state.bc_expanded_power_source_id == item_id:
                state.bc_expanded_power_source_id = ""
            elif item_id.startswith("temp_") and state.bc_expanded_temperature_id == item_id:
                state.bc_expanded_temperature_id = ""
            if state.bc_editing_id == item_id:
                state.bc_editing_id = ""
                state.bc_editing_name = ""
            if state.bc_active_assignment_id == item_id:
                _clear_assignment_focus()

    def start_bc_rename(item_id):
        """Start inline editing of a BC item name."""
        for item in state.bc_power_sources:
            if item["id"] == item_id:
                state.bc_editing_id = item_id
                state.bc_editing_name = item["name"]
                return
        for item in state.bc_temperatures:
            if item["id"] == item_id:
                state.bc_editing_id = item_id
                state.bc_editing_name = item["name"]
                return

    def finish_bc_rename(name=None):
        """Commit the inline rename and stop editing."""
        actual_name = name if name else state.bc_editing_name
        if state.bc_editing_id and actual_name:
            rename_bc_item(state.bc_editing_id, actual_name)
        state.bc_editing_id = ""

    def set_geometry_import_unit(import_id, unit):
        """Update the display unit for a geometry import."""
        state.geometry_imports = [
            {**imp, "unit": unit} if imp["id"] == import_id else imp
            for imp in (state.geometry_imports or [])
        ]
        if state.geometry_expanded_import_id == import_id:
            state.viewer_geometry_unit = unit

    server.controller.set_geometry_import_unit = set_geometry_import_unit
    server.controller.toggle_geometry_import_expanded = toggle_geometry_import_expanded
    server.controller.add_power_source = add_power_source
    server.controller.add_temperature = add_temperature
    server.controller.rename_bc_item = rename_bc_item
    server.controller.delete_bc_item = delete_bc_item
    server.controller.start_bc_rename = start_bc_rename
    server.controller.finish_bc_rename = finish_bc_rename
    server.controller.toggle_bc_item_expanded = toggle_bc_item_expanded
    server.controller.select_bc_assignment = select_bc_assignment
    server.controller.remove_selected_bc_assignment = remove_selected_bc_assignment
    server.controller.open_bc_add_placeholder = open_bc_add_placeholder
    server.controller.set_bc_item_value = set_bc_item_value
    server.controller.toggle_assign_power_source_object = toggle_assign_power_source_object
    server.controller.toggle_assign_temperature_surface = toggle_assign_temperature_surface
    server.controller.create_blank_material = create_blank_material
    server.controller.load_all_default_materials = load_all_default_materials
    server.controller.toggle_material_expanded = toggle_material_expanded
    server.controller.start_material_rename = start_material_rename
    server.controller.finish_material_rename = finish_material_rename
    server.controller.set_material_property_value = set_material_property_value

    def undo():
        if _history.undo(state):
            _log("[History] Undo")

    def redo():
        if _history.redo(state):
            _log("[History] Redo")

    server.controller.undo = undo
    server.controller.redo = redo

    with v3.VCard(
        classes="fill-height",
        flat=True,
        rounded=0,
        style="overflow-y: auto;",
    ):
        v3.VCardTitle("Model Builder", classes="text-subtitle-2 font-weight-bold pa-2")
        v3.VDivider()
        with v3.VList(
            density="compact",
            nav=True,
            mandatory=False,
            selected=("active_node ? [active_node] : []",),
        ):
            for node in MODEL_BUILDER_NODES:
                if node["id"] == "geometry":
                    # Geometry node with expandable children
                    with v3.VListGroup(value="geometry"):
                        # Geometry header
                        with html_widgets.Template(v_slot_activator="{ props }"):
                            v3.VListItem(
                                title="Geometry",
                                prepend_icon="mdi-cube-outline",
                                v_bind="props",
                                click="active_node = 'geometry'",
                            )

                        # Import button
                        v3.VListItem(
                            title="Import STEP file...",
                            prepend_icon="mdi-plus",
                            click="trigger_file_input++; active_node = 'geometry'",
                            classes="text-primary",
                            density="compact",
                        )

                elif node["id"] == "boundary_condition":
                    # Boundary Condition — expands to show Power Source and Temperature
                    with v3.VListGroup(value="boundary_condition"):
                        with html_widgets.Template(v_slot_activator="{ props }"):
                            v3.VListItem(
                                title="Boundary Condition",
                                prepend_icon="mdi-border-outside",
                                v_bind="props",
                                click="active_node = 'boundary_condition'",
                            )

                        # Power Source leaf item (items managed in Settings only)
                        v3.VListItem(
                            title="Power Source",
                            prepend_icon="mdi-flash",
                            value="bc_power_source",
                            click="active_node = 'bc_power_source'",
                            density="compact",
                        )

                        # Temperature leaf item (items managed in Settings only)
                        v3.VListItem(
                            title="Temperature",
                            prepend_icon="mdi-thermometer",
                            value="bc_temperature",
                            click="active_node = 'bc_temperature'",
                            density="compact",
                        )

                elif node["id"] == "materials":
                    # Materials — expands to show Create Blank and Add from Default
                    with v3.VListGroup(value="materials"):
                        with html_widgets.Template(v_slot_activator="{ props }"):
                            v3.VListItem(
                                title="Materials",
                                prepend_icon="mdi-atom",
                                v_bind="props",
                                click="active_node = 'materials'",
                            )

                        v3.VListItem(
                            title="Create Blank Material",
                            prepend_icon="mdi-plus",
                            click=(server.controller.create_blank_material, "[]"),
                            classes="text-primary",
                            density="compact",
                        )

                        v3.VListItem(
                            title="Add Material from Default",
                            prepend_icon="mdi-download-outline",
                            click=(server.controller.load_all_default_materials, "[]"),
                            classes="text-primary",
                            density="compact",
                        )

                else:
                    v3.VListItem(
                        title=node["title"],
                        value=node["id"],
                        prepend_icon=node["icon"],
                        click=f"active_node = active_node === '{node['id']}' ? null : '{node['id']}'",
                    )
