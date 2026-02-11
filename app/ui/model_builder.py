from trame.widgets import vuetify3 as v3, html as html_widgets

from app.engine.geometry import import_step_file

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
    # List of imported geometry files: [{id, file_name, file_path, objects (names only)}]
    state.geometry_imports = []
    state.geometry_import_counter = 0
    # Controls the file input dialog trigger
    state.trigger_file_input = 0

    # Boundary Condition items
    state.bc_power_sources = []       # [{id: "ps_1", name: "Power Source 1"}, ...]
    state.bc_temperatures = []        # [{id: "temp_1", name: "Temperature 1"}, ...]
    state.bc_power_source_counter = 0
    state.bc_temperature_counter = 0

    # Server-side storage for mesh data (not in trame state — too large)
    _geometry_meshes = {}  # import_id -> list of object dicts with vertices/triangles

    def _log(msg):
        state.log_messages = state.log_messages + [msg]

    @state.change("active_node")
    def on_node_change(active_node, **_):
        if active_node:
            _log(f"[Model Builder] Selected: {active_node}")
            # Show geometry in viewport when an import node is selected
            if active_node in _geometry_meshes:
                if hasattr(server.controller, "show_geometry"):
                    server.controller.show_geometry(_geometry_meshes[active_node])
            # Clear object highlight when switching nodes
            state.selected_object = None

    @state.change("selected_object")
    def on_object_selected(selected_object, **_):
        if hasattr(server.controller, "highlight_object"):
            server.controller.highlight_object(selected_object)

    def on_step_file_imported(file_path):
        """Called when a STEP file is selected via the server-side file input."""
        try:
            result = import_step_file(file_path)
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
            }
            state.geometry_imports = state.geometry_imports + [import_entry]
            state.active_node = import_id

            # Show geometry in viewport
            if hasattr(server.controller, "show_geometry"):
                server.controller.show_geometry(result["objects"])

            _log(f"[Geometry] Imported {result['file_name']} — {len(object_names)} objects: {', '.join(object_names)}")
        except Exception as e:
            _log(f"[Geometry] Error importing file: {e}")

    # Register the import handler on the controller so UI can call it
    server.controller.on_step_file_imported = on_step_file_imported

    def add_power_source():
        state.bc_power_source_counter = state.bc_power_source_counter + 1
        item = {"id": f"ps_{state.bc_power_source_counter}",
                "name": f"Power Source {state.bc_power_source_counter}"}
        state.bc_power_sources = state.bc_power_sources + [item]
        _log(f"[BC] Added {item['name']}")

    def add_temperature():
        state.bc_temperature_counter = state.bc_temperature_counter + 1
        item = {"id": f"temp_{state.bc_temperature_counter}",
                "name": f"Temperature {state.bc_temperature_counter}"}
        state.bc_temperatures = state.bc_temperatures + [item]
        _log(f"[BC] Added {item['name']}")

    def rename_bc_item(item_id, new_name):
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()
        if item_id.startswith("ps_"):
            items = [dict(it) for it in state.bc_power_sources]
            for it in items:
                if it["id"] == item_id:
                    it["name"] = new_name
                    break
            state.bc_power_sources = items
        elif item_id.startswith("temp_"):
            items = [dict(it) for it in state.bc_temperatures]
            for it in items:
                if it["id"] == item_id:
                    it["name"] = new_name
                    break
            state.bc_temperatures = items

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

    server.controller.add_power_source = add_power_source
    server.controller.add_temperature = add_temperature
    server.controller.rename_bc_item = rename_bc_item
    server.controller.start_bc_rename = start_bc_rename
    server.controller.finish_bc_rename = finish_bc_rename

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
                            click="trigger_file_input++",
                            classes="text-primary",
                            density="compact",
                        )

                        # Dynamic children — one per imported file
                        with html_widgets.Template(
                            v_for="(imp, idx) in geometry_imports",
                            __properties=[("v_for", "v-for")],
                        ):
                            v3.VListItem(
                                v_bind_title="imp.label + ' (' + imp.file_name + ')'",
                                v_bind_value="imp.id",
                                prepend_icon="mdi-file-cad-box",
                                click="active_node = imp.id",
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

                else:
                    v3.VListItem(
                        title=node["title"],
                        value=node["id"],
                        prepend_icon=node["icon"],
                        click=f"active_node = active_node === '{node['id']}' ? null : '{node['id']}'",
                    )
