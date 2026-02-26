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
VIEWER_SHOW_EDGES = "viewer_show_edges"              # bool, default False (always hidden)
VIEWER_SEMI_TRANSPARENT = "viewer_semi_transparent"   # bool, default False
VIEWER_WIREFRAME = "viewer_wireframe"                 # bool, default True (always on, no toolbar button)
VIEWER_WIREFRAME_ONLY = "viewer_wireframe_only"       # bool, default False; opacity=0 so only wireframe lines show
VIEWER_SHOW_RULERS = "viewer_show_rulers"             # bool, default False; toggles vtkCubeAxesActor
VIEWER_GEOMETRY_UNIT = "viewer_geometry_unit"         # str, e.g. "mm"; drives ruler axis titles

# Boundary Condition
PHYSICS_TYPE = "physics_type"                          # str, simulation type (e.g. "static_thermal")
BC_POWER_SOURCES = "bc_power_sources"                  # list of {id, name}
BC_TEMPERATURES = "bc_temperatures"                    # list of {id, name}
BC_STRESSES = "bc_stresses"                            # list of {id, name, assigned_surfaces, value}
BC_POWER_SOURCE_COUNTER = "bc_power_source_counter"    # int, auto-increment
BC_TEMPERATURE_COUNTER = "bc_temperature_counter"      # int, auto-increment
BC_STRESS_COUNTER = "bc_stress_counter"                # int, auto-increment
TIME_STEP_DURATION = "time_step_duration"              # str/float, transient simulation duration
TIME_STEP_RESOLUTION = "time_step_resolution"          # str/float, transient simulation time step size

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

# Project save / load
PROJECT_DIRTY          = "project_dirty"           # bool: unsaved changes exist
PROJECT_FILENAME       = "project_filename"         # str: suggested filename for next Save
PROJECT_ZIP_PAYLOAD    = "project_zip_payload"      # {data: base64_str, filename: str} → triggers download
PROJECT_UPLOAD_PAYLOAD = "project_upload_payload"   # {data: base64_str, filename: str} → triggers restore
OPEN_PROJECT_TRIGGER   = "open_project_trigger"     # int counter; increment to open file picker
