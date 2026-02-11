from trame.widgets import vuetify3 as v3, html as html_widgets


def create_menu_bar(server):
    state, ctrl = server.state, server.controller

    def _log(msg):
        state.log_messages = state.log_messages + [msg]

    @state.change("file_menu_action")
    def on_file_action(file_menu_action, **_):
        if file_menu_action:
            _log(f"[File] {file_menu_action}")
            state.file_menu_action = None

    @state.change("edit_menu_action")
    def on_edit_action(edit_menu_action, **_):
        if edit_menu_action:
            _log(f"[Edit] {edit_menu_action}")
            state.edit_menu_action = None

    # Blue menu bar with File/Edit on the left
    with v3.VToolbar(density="compact", color="primary", flat=True):
        with v3.VBtn(variant="text", size="small"):
            html_widgets.Span("File")
            with v3.VMenu(activator="parent"):
                with v3.VList(density="compact"):
                    v3.VListItem(
                        title="New",
                        prepend_icon="mdi-file-plus",
                        click="file_menu_action = 'New'",
                    )
                    v3.VListItem(
                        title="Open",
                        prepend_icon="mdi-folder-open",
                        click="file_menu_action = 'Open'",
                    )
                    v3.VListItem(
                        title="Save",
                        prepend_icon="mdi-content-save",
                        click="file_menu_action = 'Save'",
                    )
                    v3.VListItem(
                        title="Save As",
                        prepend_icon="mdi-content-save-edit",
                        click="file_menu_action = 'Save As'",
                    )

        with v3.VBtn(variant="text", size="small"):
            html_widgets.Span("Edit")
            with v3.VMenu(activator="parent"):
                with v3.VList(density="compact"):
                    v3.VListItem(
                        title="Undo",
                        prepend_icon="mdi-undo",
                        click="edit_menu_action = 'Undo'",
                    )
                    v3.VListItem(
                        title="Redo",
                        prepend_icon="mdi-redo",
                        click="edit_menu_action = 'Redo'",
                    )
                    v3.VListItem(
                        title="Select All",
                        prepend_icon="mdi-select-all",
                        click="edit_menu_action = 'Select All'",
                    )
                    v3.VListItem(
                        title="Clear Selection",
                        prepend_icon="mdi-select-remove",
                        click="edit_menu_action = 'Clear Selection'",
                    )

        v3.VSpacer()
