from trame.app import get_server
from trame.ui.vuetify3 import VAppLayout

from app.ui.layout import create_layout


def main():
    server = get_server(client_type="vue3")

    with VAppLayout(server, full_height=True):
        create_layout(server)

    server.start()


if __name__ == "__main__":
    main()
