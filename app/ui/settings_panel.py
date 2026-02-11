from trame.widgets import vuetify3 as v3, html as html_widgets

# Placeholder settings content per top-level node
SETTINGS_CONTENT = {
    "geometry": {
        "title": "Geometry Settings",
        "description": "Import STEP files and manage geometry objects. Click 'Import STEP file...' in the tree.",
    },
    "boundary_condition": {
        "title": "Boundary Condition Settings",
        "description": "Expand Boundary Condition in the tree to access Power Source and Temperature settings.",
    },
    "materials": {
        "title": "Material Properties",
        "description": "Adjust material properties: thermal conductivity (x, y, z), etc.",
    },
    "modelization": {
        "title": "Modelization Parameters",
        "description": "Configure how the design is divided into N sub-models.",
    },
    "build_sub_model": {
        "title": "Build Sub-Model",
        "description": "Choose FVM or AI model to generate sub-models. Output saved to server.",
    },
    "solving": {
        "title": "Solving",
        "description": "Run the solver on the built sub-models.",
    },
    "result": {
        "title": "Results",
        "description": "View simulation results. Select a run to render VTU in viewport.",
    },
}


def create_settings_panel(server):
    state = server.state
    state.settings_content = SETTINGS_CONTENT
    # ID of the BC item currently being renamed (empty = none editing)
    state.bc_editing_id = ""
    state.bc_editing_name = ""

    with v3.VCard(
        classes="fill-height",
        flat=True,
        rounded=0,
        style="overflow-y: auto;",
    ):
        v3.VCardTitle("Settings", classes="text-subtitle-2 font-weight-bold pa-2")
        v3.VDivider()

        # Show placeholder when nothing selected
        with v3.VCardText(v_if="!active_node"):
            with v3.VAlert(type="info", variant="tonal", density="compact"):
                html_widgets.Span("Select an item in Model Builder to view its settings.")

        # Show import details when a geometry import is selected (active_node starts with 'import_')
        with v3.VCardText(v_if="active_node && active_node.startsWith('import_')"):
            with html_widgets.Template(
                v_for="imp in geometry_imports",
                __properties=[("v_for", "v-for")],
            ):
                with html_widgets.Div(v_if="imp.id === active_node"):
                    v3.VCardTitle(
                        v_text="imp.label",
                        classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
                    )
                    v3.VTextField(
                        label="File",
                        v_bind_model_value="imp.file_name",
                        readonly=True,
                        variant="outlined",
                        density="compact",
                        classes="mb-2",
                    )
                    html_widgets.Div(
                        "Objects:",
                        classes="text-subtitle-2 font-weight-bold mb-1",
                    )
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            v_for="(obj, oidx) in imp.objects",
                            v_bind_key="oidx",
                            v_bind_title="obj",
                            prepend_icon="mdi-cube",
                            click="selected_object = (selected_object === obj) ? null : obj",
                            v_bind_active="selected_object === obj",
                            color="primary",
                            __properties=[("v_for", "v-for"), ("v_bind_key", ":key"), ("v_bind_active", ":active")],
                        )

        # Power Source category — list with inline rename + Add button
        with v3.VCardText(v_if="active_node === 'bc_power_source'"):
            v3.VCardTitle(
                "Power Sources",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )
            with v3.VList(density="compact"):
                with html_widgets.Template(
                    v_for="(ps, psIdx) in bc_power_sources",
                    __properties=[("v_for", "v-for")],
                ):
                    # Editing mode — show text field
                    with html_widgets.Div(
                        v_if="bc_editing_id === ps.id",
                        style="display: flex; align-items: center; padding: 4px 8px;",
                    ):
                        v3.VTextField(
                            v_model=("bc_editing_name",),
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            autofocus=True,
                            style="flex: 1;",
                            v_on_keyup_enter="$event.target.blur()",
                            blur=(server.controller.finish_bc_rename, "[bc_editing_name]"),
                            classes="bc-rename-input",
                            __properties=[("v_on_keyup_enter", "v-on:keyup.enter")],
                        )
                    # Display mode — show name as list item, double-click to edit
                    v3.VListItem(
                        v_if="bc_editing_id !== ps.id",
                        v_bind_title="ps.name",
                        prepend_icon="mdi-flash-outline",
                        dblclick=(server.controller.start_bc_rename, "[ps.id]"),
                        density="compact",
                        classes="bc-item",
                    )
            v3.VBtn(
                "Add Power Source",
                prepend_icon="mdi-plus",
                variant="tonal",
                color="primary",
                density="compact",
                classes="mt-2",
                click=(server.controller.add_power_source, "[]"),
            )

        # Temperature category — list with inline rename + Add button
        with v3.VCardText(v_if="active_node === 'bc_temperature'"):
            v3.VCardTitle(
                "Temperatures",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )
            with v3.VList(density="compact"):
                with html_widgets.Template(
                    v_for="(tmp, tmpIdx) in bc_temperatures",
                    __properties=[("v_for", "v-for")],
                ):
                    # Editing mode — show text field
                    with html_widgets.Div(
                        v_if="bc_editing_id === tmp.id",
                        style="display: flex; align-items: center; padding: 4px 8px;",
                    ):
                        v3.VTextField(
                            v_model=("bc_editing_name",),
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            autofocus=True,
                            style="flex: 1;",
                            v_on_keyup_enter="$event.target.blur()",
                            blur=(server.controller.finish_bc_rename, "[bc_editing_name]"),
                            classes="bc-rename-input",
                            __properties=[("v_on_keyup_enter", "v-on:keyup.enter")],
                        )
                    # Display mode — show name as list item, double-click to edit
                    v3.VListItem(
                        v_if="bc_editing_id !== tmp.id",
                        v_bind_title="tmp.name",
                        prepend_icon="mdi-thermometer-lines",
                        dblclick=(server.controller.start_bc_rename, "[tmp.id]"),
                        density="compact",
                        classes="bc-item",
                    )
            v3.VBtn(
                "Add Temperature",
                prepend_icon="mdi-plus",
                variant="tonal",
                color="primary",
                density="compact",
                classes="mt-2",
                click=(server.controller.add_temperature, "[]"),
            )

        # Show top-level node settings (not an import node, not a BC category)
        with v3.VCardText(
            v_if=(
                "active_node && !active_node.startsWith('import_')"
                " && active_node !== 'bc_power_source' && active_node !== 'bc_temperature'"
                " && settings_content[active_node]"
            ),
        ):
            v3.VCardTitle(
                v_text="settings_content[active_node]?.title || ''",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )
            with v3.VAlert(variant="tonal", density="compact", type="info"):
                html_widgets.Span("{{ settings_content[active_node]?.description || '' }}")
