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

        # Geometry — expandable import rows (items managed in Settings, like BC items)
        with v3.VCardText(v_if="active_node === 'geometry'"):
            v3.VCardTitle(
                "Geometry",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )
            with v3.VList(density="compact"):
                with html_widgets.Template(
                    v_for="(imp, impIdx) in geometry_imports",
                    __properties=[("v_for", "v-for")],
                ):
                    # Import row: [icon] [label (filename)] [unit select] [chevron]
                    with html_widgets.Div(
                        style="display: flex; align-items: center; gap: 6px; padding: 2px 0;",
                        classes="geo-import-row",
                    ):
                        with html_widgets.Div(style="flex: 1; min-width: 0;"):
                            v3.VListItem(
                                v_bind_title="imp.label + ' (' + imp.file_name + ')'",
                                prepend_icon="mdi-file-cad-box",
                                click=(server.controller.toggle_geometry_import_expanded, "[imp.id]"),
                                density="compact",
                                v_bind_style=(
                                    "geometry_expanded_import_id === imp.id"
                                    " ? { fontWeight: 700 } : { fontWeight: 400 }"
                                ),
                                __properties=[("v_bind_style", ":style")],
                            )
                        with html_widgets.Div(
                            classes="geo-unit-select",
                            style="width: 54px; min-width: 0; flex-shrink: 0;",
                        ):
                            v3.VSelect(
                                items=("['mm', 'm', 'cm', 'um', 'nm']",),
                                model_value=("imp.unit || 'mm'",),
                                variant="outlined",
                                density="compact",
                                hide_details=True,
                                update_modelValue=(
                                    server.controller.set_geometry_import_unit,
                                    "[imp.id, $event]",
                                ),
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color=("geometry_expanded_import_id === imp.id ? 'primary' : 'grey'",),
                            density="compact",
                            click=(server.controller.toggle_geometry_import_expanded, "[imp.id]"),
                            classes="geo-expand-btn",
                        ):
                            v3.VIcon(
                                ("geometry_expanded_import_id === imp.id ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                                size="small",
                            )
                    # Expanded body — object list
                    with html_widgets.Div(
                        v_if="geometry_expanded_import_id === imp.id",
                        style=(
                            "border: 1px solid #e0e0e0; border-radius: 6px; margin: 4px 8px 8px 8px;"
                            " padding: 8px;"
                        ),
                        classes="geo-expanded-body",
                    ):
                        html_widgets.Div(
                            "Objects:",
                            classes="text-caption font-weight-bold mb-1",
                        )
                        with v3.VList(density="compact"):
                            v3.VListItem(
                                title="No objects",
                                v_if="!imp.objects || imp.objects.length === 0",
                                density="compact",
                                disabled=True,
                            )
                            with html_widgets.Template(
                                v_for="(obj, oidx) in imp.objects",
                                __properties=[("v_for", "v-for")],
                            ):
                                v3.VListItem(
                                    v_bind_title="obj",
                                    prepend_icon="mdi-cube",
                                    density="compact",
                                    click="selected_object = (selected_object === obj) ? null : obj",
                                    v_bind_active="selected_object === obj",
                                    color="primary",
                                    __properties=[("v_bind_active", ":active")],
                                )

        # Materials — collapsible list of project materials
        with v3.VCardText(v_if="active_node === 'materials'"):
            v3.VCardTitle(
                "Materials",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )

            # Status message
            with v3.VAlert(
                v_if="materials_last_result",
                type="info",
                variant="tonal",
                density="compact",
                classes="mb-2",
            ):
                html_widgets.Span("{{ materials_last_result }}")

            # Project materials list
            with v3.VList(density="compact"):
                with html_widgets.Template(
                    v_for="(mat, matIdx) in materials_items",
                    __properties=[("v_for", "v-for")],
                ):
                    # Editing mode — inline rename text field
                    with html_widgets.Div(
                        v_if="materials_editing_id === mat.name",
                        style="display: flex; align-items: center; padding: 4px 8px;",
                    ):
                        v3.VTextField(
                            v_model=("materials_editing_name",),
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            autofocus=True,
                            style="flex: 1;",
                            v_on_keyup_enter="$event.target.blur()",
                            blur=(server.controller.finish_material_rename, "[materials_editing_name]"),
                            classes="material-rename-input",
                            __properties=[("v_on_keyup_enter", "v-on:keyup.enter")],
                        )

                    # Display mode — name row + chevron
                    with html_widgets.Div(
                        v_if="materials_editing_id !== mat.name",
                        style="display: flex; align-items: center; gap: 6px; padding: 2px 0;",
                        classes="material-item-row",
                    ):
                        with html_widgets.Div(style="flex: 1; min-width: 0;"):
                            v3.VListItem(
                                v_bind_title="mat.name",
                                prepend_icon="mdi-atom",
                                click=(server.controller.toggle_material_expanded, "[mat.name]"),
                                dblclick=(server.controller.start_material_rename, "[mat.name]"),
                                density="compact",
                                v_bind_style=(
                                    "materials_expanded_item === mat.name"
                                    " ? { fontWeight: 700 } : { fontWeight: 400 }"
                                ),
                                __properties=[("v_bind_style", ":style")],
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color=("materials_expanded_item === mat.name ? 'primary' : 'grey'",),
                            density="compact",
                            click=(server.controller.toggle_material_expanded, "[mat.name]"),
                            classes="material-expand-btn",
                        ):
                            v3.VIcon(
                                ("materials_expanded_item === mat.name ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                                size="small",
                            )

                    # Expanded body — structured property rows
                    with html_widgets.Div(
                        v_if="materials_expanded_item === mat.name && materials_editing_id !== mat.name",
                        style=(
                            "border: 1px solid #e0e0e0; border-radius: 6px;"
                            " margin: 4px 8px 8px 8px; padding: 8px;"
                        ),
                        classes="material-expanded-body",
                    ):
                        with html_widgets.Template(
                            v_for="(propVal, propName) in mat.properties",
                            __properties=[("v_for", "v-for")],
                        ):
                            # Tensor property (value is array) — one row per component
                            with html_widgets.Template(
                                v_if="Array.isArray(propVal.value)",
                            ):
                                with html_widgets.Template(
                                    v_for="(compVal, compIdx) in propVal.value",
                                    __properties=[("v_for", "v-for")],
                                ):
                                    with html_widgets.Div(
                                        style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;",
                                    ):
                                        html_widgets.Span(
                                            "{{ propName.replace(/_/g, ' ').replace(/^\\w/, c => c.toUpperCase()) }}"
                                            " - {{ ['x','y','z'][compIdx] }} :",
                                            style="font-size: 12px; min-width: 200px;",
                                        )
                                        v3.VTextField(
                                            model_value=("compVal",),
                                            type="number",
                                            variant="outlined",
                                            density="compact",
                                            hide_details=True,
                                            style="max-width: 100px;",
                                            blur=(
                                                server.controller.set_material_property_value,
                                                "[mat.name, propName, compIdx, $event.target.value]",
                                            ),
                                            classes="material-prop-input",
                                        )
                                        html_widgets.Span(
                                            "{{ propVal.units }}",
                                            style="font-size: 12px; color: #555;",
                                            v_if="propVal.units",
                                        )
                            # Scalar property — single row
                            with html_widgets.Template(
                                v_if="!Array.isArray(propVal.value)",
                            ):
                                with html_widgets.Div(
                                    style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;",
                                ):
                                    html_widgets.Span(
                                        "{{ propName.replace(/_/g, ' ').replace(/^\\w/, c => c.toUpperCase()) }} :",
                                        style="font-size: 12px; min-width: 200px;",
                                    )
                                    v3.VTextField(
                                        model_value=("propVal.value",),
                                        type="number",
                                        variant="outlined",
                                        density="compact",
                                        hide_details=True,
                                        style="max-width: 100px;",
                                        blur=(
                                            server.controller.set_material_property_value,
                                            "[mat.name, propName, -1, $event.target.value]",
                                        ),
                                        classes="material-prop-input",
                                    )
                                    html_widgets.Span(
                                        "{{ propVal.units }}",
                                        style="font-size: 12px; color: #555;",
                                        v_if="propVal.units",
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
                    with html_widgets.Div(
                        v_if="bc_editing_id !== ps.id",
                        style="display: flex; align-items: center; gap: 6px; padding: 2px 0;",
                        classes="bc-item-row",
                    ):
                        with html_widgets.Div(style="flex: 1; min-width: 0;"):
                            v3.VListItem(
                                v_bind_title="ps.name",
                                prepend_icon="mdi-flash-outline",
                                click=(server.controller.toggle_bc_item_expanded, "[ps.id]"),
                                dblclick=(server.controller.start_bc_rename, "[ps.id]"),
                                density="compact",
                                classes="bc-item",
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color=("bc_expanded_power_source_id === ps.id ? 'primary' : 'grey'",),
                            density="compact",
                            click=(server.controller.toggle_bc_item_expanded, "[ps.id]"),
                            classes="bc-expand-btn",
                        ):
                            v3.VIcon(
                                ("bc_expanded_power_source_id === ps.id ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                                size="small",
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color="grey-lighten-1",
                            density="compact",
                            click=(server.controller.delete_bc_item, "[ps.id]"),
                            classes="bc-delete-btn",
                        ):
                            v3.VIcon("mdi-delete-outline", color="grey-lighten-1")
                    with html_widgets.Div(
                        v_if="bc_expanded_power_source_id === ps.id",
                        style=(
                            "border: 1px solid #e0e0e0; border-radius: 6px; margin: 4px 8px 8px 8px;"
                            " padding: 8px;"
                        ),
                        classes="bc-expanded-body",
                    ):
                        v3.VTextField(
                            label="Power (W/m)",
                            type="number",
                            v_bind_model_value="ps.power",
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            classes="bc-power-input mb-2",
                            blur=(server.controller.set_bc_item_value, "[ps.id, 'power', $event.target.value]"),
                        )
                        with html_widgets.Div(
                            style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;",
                        ):
                            html_widgets.Div("Assigned Objects", classes="text-caption font-weight-bold")
                            with html_widgets.Div(style="display: flex; gap: 4px;"):
                                with v3.VBtn(
                                    icon=True,
                                    variant="text",
                                    density="compact",
                                    click=(server.controller.open_bc_add_placeholder, "[ps.id]"),
                                    classes="bc-assign-add-btn",
                                ):
                                    v3.VIcon("mdi-plus", size="small")
                                with v3.VBtn(
                                    icon=True,
                                    variant="text",
                                    density="compact",
                                    click=(server.controller.remove_selected_bc_assignment, "[ps.id]"),
                                    classes="bc-assign-remove-btn",
                                ):
                                    v3.VIcon("mdi-minus", size="small")
                        with v3.VList(
                            density="compact",
                            style=(
                                "border: 1px solid #d8d8d8; border-radius: 4px;"
                                " height: 180px; overflow-y: auto;"
                            ),
                            classes="bc-assignment-list",
                        ):
                            v3.VListItem(
                                title="No objects assigned",
                                v_if="!ps.assigned_objects || ps.assigned_objects.length === 0",
                                density="compact",
                                disabled=True,
                            )
                            with html_widgets.Template(
                                v_for="(objName, objIdx) in ps.assigned_objects",
                                __properties=[("v_for", "v-for")],
                            ):
                                v3.VListItem(
                                    v_bind_title="objName",
                                    density="compact",
                                    style="min-height: 24px; padding-top: 2px; padding-bottom: 2px; font-size: 12px;",
                                    click=(
                                        server.controller.select_bc_assignment,
                                        "[ps.id, objName, objIdx, $event.shiftKey, ($event.ctrlKey || $event.metaKey)]",
                                    ),
                                    v_bind_active=(
                                        "bc_selected_assignment_item_id === ps.id && "
                                        "(bc_selected_assignment_values || []).includes(objName)"
                                    ),
                                    __properties=[("v_bind_active", ":active")],
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
                    with html_widgets.Div(
                        v_if="bc_editing_id !== tmp.id",
                        style="display: flex; align-items: center; gap: 6px; padding: 2px 0;",
                        classes="bc-item-row",
                    ):
                        with html_widgets.Div(style="flex: 1; min-width: 0;"):
                            v3.VListItem(
                                v_bind_title="tmp.name",
                                prepend_icon="mdi-thermometer-lines",
                                click=(server.controller.toggle_bc_item_expanded, "[tmp.id]"),
                                dblclick=(server.controller.start_bc_rename, "[tmp.id]"),
                                density="compact",
                                classes="bc-item",
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color=("bc_expanded_temperature_id === tmp.id ? 'primary' : 'grey'",),
                            density="compact",
                            click=(server.controller.toggle_bc_item_expanded, "[tmp.id]"),
                            classes="bc-expand-btn",
                        ):
                            v3.VIcon(
                                ("bc_expanded_temperature_id === tmp.id ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                                size="small",
                            )
                        with v3.VBtn(
                            icon=True,
                            variant="text",
                            color="grey-lighten-1",
                            density="compact",
                            click=(server.controller.delete_bc_item, "[tmp.id]"),
                            classes="bc-delete-btn",
                        ):
                            v3.VIcon("mdi-delete-outline", color="grey-lighten-1")
                    with html_widgets.Div(
                        v_if="bc_expanded_temperature_id === tmp.id",
                        style=(
                            "border: 1px solid #e0e0e0; border-radius: 6px; margin: 4px 8px 8px 8px;"
                            " padding: 8px;"
                        ),
                        classes="bc-expanded-body",
                    ):
                        v3.VTextField(
                            label="Temperature (oC)",
                            type="number",
                            v_bind_model_value="tmp.temperature",
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            classes="bc-temperature-input mb-2",
                            blur=(server.controller.set_bc_item_value, "[tmp.id, 'temperature', $event.target.value]"),
                        )
                        with html_widgets.Div(
                            style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;",
                        ):
                            html_widgets.Div("Assigned Surfaces", classes="text-caption font-weight-bold")
                            with html_widgets.Div(style="display: flex; gap: 4px;"):
                                with v3.VBtn(
                                    icon=True,
                                    variant="text",
                                    density="compact",
                                    click=(server.controller.open_bc_add_placeholder, "[tmp.id]"),
                                    classes="bc-assign-add-btn",
                                ):
                                    v3.VIcon("mdi-plus", size="small")
                                with v3.VBtn(
                                    icon=True,
                                    variant="text",
                                    density="compact",
                                    click=(server.controller.remove_selected_bc_assignment, "[tmp.id]"),
                                    classes="bc-assign-remove-btn",
                                ):
                                    v3.VIcon("mdi-minus", size="small")
                        with v3.VList(
                            density="compact",
                            style=(
                                "border: 1px solid #d8d8d8; border-radius: 4px;"
                                " height: 180px; overflow-y: auto;"
                            ),
                            classes="bc-assignment-list",
                        ):
                            v3.VListItem(
                                title="No surfaces assigned",
                                v_if="!tmp.assigned_surfaces || tmp.assigned_surfaces.length === 0",
                                density="compact",
                                disabled=True,
                            )
                            with html_widgets.Template(
                                v_for="(surfaceName, surfaceIdx) in tmp.assigned_surfaces",
                                __properties=[("v_for", "v-for")],
                            ):
                                v3.VListItem(
                                    v_bind_title="surfaceName",
                                    density="compact",
                                    style="min-height: 24px; padding-top: 2px; padding-bottom: 2px; font-size: 12px;",
                                    click=(
                                        server.controller.select_bc_assignment,
                                        "[tmp.id, surfaceName, surfaceIdx, $event.shiftKey, ($event.ctrlKey || $event.metaKey)]",
                                    ),
                                    v_bind_active=(
                                        "bc_selected_assignment_item_id === tmp.id && "
                                        "(bc_selected_assignment_values || []).includes(surfaceName)"
                                    ),
                                    __properties=[("v_bind_active", ":active")],
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

        # Show top-level node settings (not geometry, not a BC category)
        with v3.VCardText(
            v_if=(
                "active_node && active_node !== 'geometry'"
                " && active_node !== 'bc_power_source' && active_node !== 'bc_temperature'"
                " && active_node !== 'materials'"
                " && settings_content[active_node]"
            ),
        ):
            v3.VCardTitle(
                v_text="settings_content[active_node]?.title || ''",
                classes="text-subtitle-1 font-weight-bold pa-0 mb-2",
            )
            with v3.VAlert(variant="tonal", density="compact", type="info"):
                html_widgets.Span("{{ settings_content[active_node]?.description || '' }}")

        with v3.VDialog(
            v_model=("show_bc_add_placeholder",),
            max_width="460",
        ):
            with v3.VCard():
                v3.VCardTitle("Not Implemented", classes="text-subtitle-1")
                with v3.VCardText():
                    html_widgets.Span("{{ bc_add_placeholder_message }}")
                with v3.VCardActions():
                    v3.VSpacer()
                    v3.VBtn(
                        "OK",
                        color="primary",
                        variant="text",
                        click="show_bc_add_placeholder = false",
                    )
