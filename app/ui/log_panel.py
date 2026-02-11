from trame.widgets import vuetify3 as v3


def create_log_panel(server):
    state = server.state

    with v3.VCard(
        flat=True,
        rounded=0,
        style="overflow-y: auto; max-height: 100%; font-family: monospace; font-size: 12px;",
        classes="fill-height",
    ):
        v3.VCardTitle("Log", classes="text-subtitle-2 font-weight-bold pa-2")
        v3.VDivider()
        with v3.VCardText(classes="pa-2"):
            with v3.VList(density="compact"):
                with v3.VListItem(
                    v_for="(msg, idx) in log_messages",
                    key="idx",
                    classes="pa-0",
                    style="min-height: 20px;",
                ):
                    html_text = "{{ msg }}"
