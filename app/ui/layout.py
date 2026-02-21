import os

from trame.widgets import vuetify3 as v3, html as html_widgets

from app.ui.menu_bar import create_menu_bar
from app.ui.model_builder import create_model_builder
from app.ui.settings_panel import create_settings_panel
from app.ui.viewer import create_viewer
from app.ui.log_panel import create_log_panel


def create_layout(server):
    state = server.state

    # Initialize state defaults
    state.show_left_panels = True
    state.show_settings = True
    state.show_log_panel = True
    state.model_builder_width = 220
    state.settings_width = 280
    state.dragging_handle = None
    state.drag_start_x = 0
    state.drag_start_width = 0
    state.log_messages = ["[System] Application started."]
    state.active_node = None
    state.file_menu_action = None
    state.edit_menu_action = None
    # File import dialog + file browser
    state.show_import_dialog = False
    state.import_file_path = ""
    state.browse_current_dir = os.path.expanduser("~")
    state.browse_entries = []
    state.browse_go_up_trigger = 0

    def _refresh_browse_entries():
        """List directories and .step/.stp files in browse_current_dir."""
        dir_path = state.browse_current_dir
        try:
            dirs = []
            files = []
            for name in sorted(os.listdir(dir_path)):
                if name.startswith("."):
                    continue
                full = os.path.join(dir_path, name)
                if os.path.isdir(full):
                    dirs.append({"name": name, "is_dir": True, "full_path": full})
                elif name.lower().endswith((".step", ".stp")):
                    files.append({"name": name, "is_dir": False, "full_path": full})
            state.browse_entries = dirs + files
        except PermissionError:
            state.browse_entries = []

    # Watch for import trigger from Model Builder
    @state.change("trigger_file_input")
    def _on_trigger_import(trigger_file_input, **_):
        if trigger_file_input:
            state.import_file_path = ""
            state.show_import_dialog = True
            _refresh_browse_entries()

    @state.change("browse_current_dir")
    def _on_browse_dir_change(browse_current_dir, **_):
        if state.show_import_dialog and browse_current_dir:
            state.import_file_path = ""
            _refresh_browse_entries()

    @state.change("browse_go_up_trigger")
    def _on_browse_go_up(browse_go_up_trigger, **_):
        if browse_go_up_trigger:
            parent = os.path.dirname(state.browse_current_dir)
            if parent and parent != state.browse_current_dir:
                state.browse_current_dir = parent

    state.do_import_trigger = 0

    @state.change("do_import_trigger")
    def _on_do_import(do_import_trigger, **_):
        if do_import_trigger:
            path = state.import_file_path.strip()
            if path:
                server.controller.on_step_file_imported(path)
            state.show_import_dialog = False
            state.import_file_path = ""

    # Full-height flex column — no VMain padding
    # tabindex="-1" makes it programmatically focusable so @keydown fires for
    # global shortcuts (Ctrl+Z / Ctrl+Y) when no text field has focus.
    with html_widgets.Div(
        style="height: 100vh; display: flex; flex-direction: column; overflow: hidden;",
        tabindex="-1",
        keydown=(
            "const tag = $event.target.tagName.toLowerCase();"
            " const editable = tag === 'input' || tag === 'textarea' || $event.target.isContentEditable;"
            " if ($event.ctrlKey && !$event.shiftKey && $event.key === 'z' && !editable)"
            "   { $event.preventDefault(); edit_menu_action = 'Undo'; }"
            " else if ($event.ctrlKey && ($event.key === 'y' || ($event.shiftKey && $event.key === 'z')) && !editable)"
            "   { $event.preventDefault(); edit_menu_action = 'Redo'; }"
        ),
    ):

        # White title bar above menu — narrow, text fills ~85% of height
        with html_widgets.Div(
            style="background: white; padding: 0 12px; border-bottom: 1px solid #e0e0e0; flex: 0 0 30px; display: flex; align-items: center;",
        ):
            html_widgets.Div(
                "DS WebApp",
                style="font-size: 16px; font-weight: bold; line-height: 1;",
            )

        # Blue menu bar
        create_menu_bar(server)

        # Top section: left panels + viewport
        with html_widgets.Div(
            style="display: flex; flex: 1 1 auto; overflow: hidden; min-height: 0;",
        ):
            # Model Builder panel (visible when left panels are open)
            with html_widgets.Div(
                v_show="show_left_panels",
                style="display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0;",
                v_bind_style=("{ width: model_builder_width + 'px' }",),
            ):
                create_model_builder(server)

            # Drag handle between Model Builder and Settings panels
            html_widgets.Div(
                v_show="show_left_panels && show_settings",
                style="width: 5px; flex: 0 0 5px; cursor: col-resize; background: #e0e0e0; z-index: 10; user-select: none;",
                mousedown="dragging_handle = 'mb'; drag_start_x = $event.clientX; drag_start_width = model_builder_width; $event.preventDefault()",
            )

            # Settings panel (visible when left panels are open AND settings toggled on)
            with html_widgets.Div(
                v_show="show_left_panels && show_settings",
                style="display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0;",
                v_bind_style=("{ width: settings_width + 'px' }",),
            ):
                create_settings_panel(server)

            # Drag handle between Settings panel and Viewport
            html_widgets.Div(
                v_show="show_left_panels && show_settings",
                style="width: 5px; flex: 0 0 5px; cursor: col-resize; background: #e0e0e0; z-index: 10; user-select: none;",
                mousedown="dragging_handle = 'settings'; drag_start_x = $event.clientX; drag_start_width = settings_width; $event.preventDefault()",
            )

            # Center viewport
            with html_widgets.Div(
                style="flex: 1 1 auto; overflow: hidden; display: flex; flex-direction: column; min-width: 0;",
            ):
                # Toolbar with panel toggle buttons
                with v3.VToolbar(density="compact", flat=True, color="grey-lighten-4"):
                    with v3.VBtn(
                        icon=True,
                        click="show_left_panels = !show_left_panels",
                        variant="text",
                        size="small",
                        classes="toggle-model-builder",
                    ):
                        v3.VIcon(
                            "mdi-arrow-collapse-left",
                            v_if="show_left_panels",
                            size="small",
                        )
                        v3.VIcon(
                            "mdi-arrow-expand-right",
                            v_if="!show_left_panels",
                            size="small",
                        )
                    with v3.VBtn(
                        icon=True,
                        click="show_settings = !show_settings",
                        variant="text",
                        size="small",
                        classes="toggle-settings",
                    ):
                        v3.VIcon("mdi-cog", size="small")

                    v3.VDivider(vertical=True, classes="mx-1")

                    # Viewer display mode toggles
                    with v3.VBtn(
                        icon=True,
                        click="viewer_show_rulers = !viewer_show_rulers",
                        variant="text",
                        size="small",
                        classes="toggle-rulers",
                    ):
                        v3.VIcon(
                            "mdi-ruler",
                            size="small",
                            color=("viewer_show_rulers ? 'blue' : ''",),
                        )
                    with v3.VBtn(
                        icon=True,
                        click="viewer_semi_transparent = !viewer_semi_transparent; if (viewer_semi_transparent) viewer_wireframe_only = false",
                        variant="text",
                        size="small",
                        classes="toggle-semi-transparent",
                    ):
                        v3.VIcon(
                            "mdi-circle-half-full",
                            size="small",
                            color=("viewer_semi_transparent ? 'blue' : ''",),
                        )
                    with v3.VBtn(
                        icon=True,
                        click="viewer_wireframe_only = !viewer_wireframe_only; if (viewer_wireframe_only) viewer_semi_transparent = false",
                        variant="text",
                        size="small",
                        classes="toggle-wireframe",
                    ):
                        v3.VIcon(
                            "mdi-cube-outline",
                            size="small",
                            color=("viewer_wireframe_only ? 'blue' : ''",),
                        )
                    with v3.VBtn(
                        icon=True,
                        click="viewer_scene_light = !viewer_scene_light",
                        variant="text",
                        size="small",
                        classes="toggle-scene-light",
                    ):
                        v3.VIcon(
                            "mdi-lightbulb-outline",
                            size="small",
                            color=("viewer_scene_light ? 'blue' : ''",),
                        )

                    v3.VSpacer()
                    with v3.VBtn(
                        icon=True,
                        click="show_log_panel = !show_log_panel",
                        variant="text",
                        size="small",
                        classes="toggle-log",
                    ):
                        v3.VIcon("mdi-console", size="small")

                # VTK Viewer
                with html_widgets.Div(style="flex: 1 1 auto; min-height: 0;"):
                    create_viewer(server)

        # Bottom log panel
        with html_widgets.Div(
            v_show="show_log_panel",
            style="height: 160px; border-top: 2px solid #e0e0e0; flex: 0 0 auto;",
        ):
            create_log_panel(server)

        # STEP file import dialog with file browser
        with v3.VDialog(
            v_model=("show_import_dialog",),
            max_width="600",
            persistent=True,
        ):
            with v3.VCard():
                v3.VCardTitle("Import STEP File", classes="text-subtitle-1")
                with v3.VCardText(classes="pa-2"):
                    # Path bar with up button
                    with html_widgets.Div(
                        style="display: flex; align-items: center; gap: 4px; margin-bottom: 8px;",
                    ):
                        v3.VBtn(
                            icon=True,
                            variant="text",
                            size="x-small",
                            click="browse_go_up_trigger++",
                            classes="browse-up-btn",
                        )
                        v3.VIcon("mdi-arrow-up", size="small", click="browse_go_up_trigger++")
                        v3.VTextField(
                            v_model=("browse_current_dir",),
                            variant="outlined",
                            density="compact",
                            hide_details=True,
                            classes="browse-path-input",
                            style="font-size: 12px;",
                        )
                    # File list
                    with v3.VList(
                        density="compact",
                        style="max-height: 350px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 4px;",
                        classes="browse-file-list",
                    ):
                        # Empty state
                        v3.VListItem(
                            title="No STEP files or folders found",
                            v_if="browse_entries.length === 0",
                            disabled=True,
                        )
                        # Directory and file entries
                        with html_widgets.Template(
                            v_for="(entry, idx) in browse_entries",
                            __properties=[("v_for", "v-for")],
                        ):
                            v3.VListItem(
                                v_bind_title="entry.name",
                                prepend_icon=("entry.is_dir ? 'mdi-folder' : 'mdi-file-cad-box'",),
                                click="entry.is_dir ? (browse_current_dir = entry.full_path) : (import_file_path = entry.full_path)",
                                active=("entry.full_path === import_file_path",),
                                color=("entry.full_path === import_file_path ? 'primary' : ''",),
                                classes="browse-entry",
                            )
                    # Selected file display
                    with html_widgets.Div(
                        v_show="import_file_path",
                        style="margin-top: 8px; font-size: 12px; color: #1976D2;",
                    ):
                        html_widgets.Span("Selected: ")
                        html_widgets.Span(
                            "{{ import_file_path }}",
                            style="font-weight: 500;",
                        )
                with v3.VCardActions():
                    v3.VSpacer()
                    v3.VBtn(
                        "Cancel",
                        variant="text",
                        click="show_import_dialog = false; import_file_path = ''",
                    )
                    v3.VBtn(
                        "Import",
                        color="primary",
                        variant="flat",
                        click="do_import_trigger++",
                        disabled=("!import_file_path",),
                        classes="import-confirm-btn",
                    )

        # Transparent overlay active during panel resize drag — prevents
        # mouse events reaching the VTK viewport or other elements mid-drag
        html_widgets.Div(
            v_show="dragging_handle",
            style="position: fixed; inset: 0; z-index: 9999; cursor: col-resize; user-select: none;",
            mousemove=(
                "dragging_handle === 'mb'"
                " ? (model_builder_width = Math.max(120, Math.min(500, drag_start_width + $event.clientX - drag_start_x)))"
                " : (settings_width = Math.max(120, Math.min(600, drag_start_width + $event.clientX - drag_start_x)))"
            ),
            mouseup="dragging_handle = null",
        )
