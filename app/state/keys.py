# Central registry of trame state key names

# Panel visibility
SHOW_LEFT_PANELS = "show_left_panels"
SHOW_SETTINGS = "show_settings"
SHOW_LOG_PANEL = "show_log_panel"

# Model Builder selection
ACTIVE_NODE = "active_node"  # currently selected tree node id

# Geometry object selection
SELECTED_OBJECT = "selected_object"  # name of highlighted object in viewport

# Viewer display modes
VIEWER_SHOW_EDGES = "viewer_show_edges"              # bool, default True
VIEWER_SEMI_TRANSPARENT = "viewer_semi_transparent"   # bool, default False
VIEWER_WIREFRAME = "viewer_wireframe"                 # bool, default False

# Boundary Condition
BC_POWER_SOURCES = "bc_power_sources"                  # list of {id, name}
BC_TEMPERATURES = "bc_temperatures"                    # list of {id, name}
BC_POWER_SOURCE_COUNTER = "bc_power_source_counter"    # int, auto-increment
BC_TEMPERATURE_COUNTER = "bc_temperature_counter"      # int, auto-increment

# Materials
MATERIALS_CATALOG = "materials_catalog"          # list of {name, kind, default_units, symmetry} from API
MATERIALS_ITEMS = "materials_items"              # list of project materials: [{name, properties}]
MATERIALS_EXPANDED_ITEM = "materials_expanded_item"  # name of the currently expanded material row
MATERIALS_EDITING_ID = "materials_editing_id"    # name of material currently being renamed (empty = none)
MATERIALS_EDITING_NAME = "materials_editing_name"  # current text in rename input
MATERIALS_COUNTER = "materials_counter"          # int, auto-increment for blank material names
MATERIALS_LAST_RESULT = "materials_last_result"  # latest status message

# Log
LOG_MESSAGES = "log_messages"
