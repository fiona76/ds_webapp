from trame.widgets import vuetify3 as v3, html as html_widgets

try:
    from trame.widgets import vtk as vtk_widgets
    from vtkmodules.vtkRenderingCore import (
        vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor,
        vtkPolyDataMapper, vtkActor,
    )
    from vtkmodules.vtkCommonCore import vtkPoints
    from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray, vtkTriangle, vtkLine
    from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
    from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
    # Ensure OpenGL2 backend is loaded
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False

# Background
BG_COLOR = (0.85, 0.91, 0.97)  # very light blue

# Default and highlight colors (darker objects for light background)
COLOR_DEFAULT = (0.35, 0.52, 0.72)
COLOR_HIGHLIGHT = (1.0, 0.6, 0.15)
EDGE_DEFAULT = (0.15, 0.15, 0.15)
EDGE_HIGHLIGHT = (0.8, 0.4, 0.0)


def _object_to_vtk_polydata(obj):
    """Convert a single geometry object (with vertices/triangles) to vtkPolyData."""
    points = vtkPoints()
    for v in obj["vertices"]:
        points.InsertNextPoint(v[0], v[1], v[2])

    cells = vtkCellArray()
    for tri in obj["triangles"]:
        triangle = vtkTriangle()
        triangle.GetPointIds().SetId(0, tri[0])
        triangle.GetPointIds().SetId(1, tri[1])
        triangle.GetPointIds().SetId(2, tri[2])
        cells.InsertNextCell(triangle)

    poly = vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)

    normals = vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.ComputePointNormalsOn()
    normals.Update()

    return normals.GetOutput()


def _edges_to_vtk_polydata(edge_polylines):
    """Convert a list of edge polylines to vtkPolyData with line cells."""
    points = vtkPoints()
    cells = vtkCellArray()

    for polyline in edge_polylines:
        if len(polyline) < 2:
            continue
        start_idx = points.GetNumberOfPoints()
        for pt in polyline:
            points.InsertNextPoint(pt[0], pt[1], pt[2])
        for i in range(len(polyline) - 1):
            line = vtkLine()
            line.GetPointIds().SetId(0, start_idx + i)
            line.GetPointIds().SetId(1, start_idx + i + 1)
            cells.InsertNextCell(line)

    poly = vtkPolyData()
    poly.SetPoints(points)
    poly.SetLines(cells)
    return poly


def create_viewer(server):
    state = server.state

    if VTK_AVAILABLE:
        renderer = vtkRenderer()
        renderer.SetBackground(*BG_COLOR)
        render_window = vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetOffScreenRendering(1)

        rw_interactor = vtkRenderWindowInteractor()
        rw_interactor.SetRenderWindow(render_window)
        rw_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        # Per-object actors: {name: vtkActor}
        current_actors = {}
        # Per-object feature edge actors: {name: vtkActor}
        edge_actors = {}
        # Reverse mapping: {scene_object_id: object_name} for click-to-pick
        actor_id_to_name = {}
        # Will be set once VtkLocalView is created
        _get_scene_object_id = None

        # Initialize viewer display mode defaults
        state.viewer_show_edges = True
        state.viewer_semi_transparent = False
        state.viewer_wireframe = True
        state.viewer_scene_light = True

        def _style_actor(actor, highlighted=False, show_edges=True,
                         semi_transparent=False, scene_light=True):
            prop = actor.GetProperty()
            if highlighted:
                prop.SetColor(*COLOR_HIGHLIGHT)
                prop.SetEdgeColor(*EDGE_HIGHLIGHT)
                prop.SetLineWidth(1.5)
            else:
                prop.SetColor(*COLOR_DEFAULT)
                prop.SetEdgeColor(*EDGE_DEFAULT)
                prop.SetLineWidth(0.5)
            prop.SetRepresentationToSurface()
            prop.SetEdgeVisibility(show_edges)
            prop.SetOpacity(0.4 if semi_transparent else 1.0)
            if scene_light:
                prop.SetAmbient(0.2)
                prop.SetDiffuse(0.8)
            else:
                prop.SetAmbient(1.0)
                prop.SetDiffuse(0.0)

        def show_geometry(objects):
            """Display geometry objects in the viewport, one actor per object."""
            # Remove all previous actors
            for actor in current_actors.values():
                renderer.RemoveActor(actor)
            current_actors.clear()
            for actor in edge_actors.values():
                renderer.RemoveActor(actor)
            edge_actors.clear()
            actor_id_to_name.clear()

            if not objects:
                server.controller.view_update()
                return

            for obj in objects:
                # Surface actor
                polydata = _object_to_vtk_polydata(obj)
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(polydata)
                actor = vtkActor()
                actor.SetMapper(mapper)
                _style_actor(
                    actor,
                    highlighted=False,
                    show_edges=state.viewer_show_edges,
                    semi_transparent=state.viewer_semi_transparent,
                    scene_light=state.viewer_scene_light,
                )
                renderer.AddActor(actor)
                current_actors[obj["name"]] = actor
                # Build picking map using the view's scene object ID
                if _get_scene_object_id is not None:
                    actor_id_to_name[_get_scene_object_id(actor)] = obj["name"]

                # Feature edge actor
                edge_polylines = obj.get("edges", [])
                if edge_polylines:
                    edge_pd = _edges_to_vtk_polydata(edge_polylines)
                    edge_mapper = vtkPolyDataMapper()
                    edge_mapper.SetInputData(edge_pd)
                    edge_actor = vtkActor()
                    edge_actor.SetMapper(edge_mapper)
                    prop = edge_actor.GetProperty()
                    prop.SetColor(*EDGE_DEFAULT)
                    prop.SetLineWidth(2.0)
                    prop.SetOpacity(1.0)
                    edge_actor.SetVisibility(state.viewer_wireframe)
                    renderer.AddActor(edge_actor)
                    edge_actors[obj["name"]] = edge_actor

            renderer.ResetCamera()
            server.controller.view_update()

        def _apply_all_styles(*args):
            """Re-style every actor based on current selection + display mode state."""
            selected = state.selected_object
            show_edges = state.viewer_show_edges
            semi_trans = state.viewer_semi_transparent
            wireframe = state.viewer_wireframe
            scene_light = state.viewer_scene_light

            for obj_name, actor in current_actors.items():
                is_highlighted = (obj_name == selected)
                if selected is None:
                    obj_semi = semi_trans
                elif obj_name == selected:
                    obj_semi = False
                else:
                    obj_semi = semi_trans
                _style_actor(
                    actor,
                    highlighted=is_highlighted,
                    show_edges=show_edges,
                    semi_transparent=obj_semi,
                    scene_light=scene_light,
                )

            # Toggle feature edge actors
            for obj_name, edge_actor in edge_actors.items():
                edge_actor.SetVisibility(wireframe)
                prop = edge_actor.GetProperty()
                if obj_name == selected:
                    prop.SetColor(*EDGE_HIGHLIGHT)
                else:
                    prop.SetColor(*EDGE_DEFAULT)

            server.controller.view_update()

        @state.change("viewer_show_edges", "viewer_semi_transparent", "viewer_wireframe", "viewer_scene_light")
        def _on_viewer_mode_change(**_):
            if current_actors:
                _apply_all_styles()

        def on_click(event):
            """Handle click-to-pick on the 3D viewport."""
            if event is None:
                state.selected_object = None
                return
            remote_id = event.get("remoteId")
            name = actor_id_to_name.get(remote_id) if remote_id else None
            state.selected_object = name

        def reset_view():
            """Reset the camera to fit all geometry in the viewport."""
            renderer.ResetCamera()
            server.controller.view_reset_camera()

        server.controller.show_geometry = show_geometry
        server.controller.highlight_object = _apply_all_styles
        server.controller.reset_view = reset_view

        with v3.VCard(classes="fill-height", flat=True, rounded=0):
            with v3.VCardText(classes="pa-0 fill-height", style="position: relative;"):
                with vtk_widgets.VtkLocalView(
                    render_window,
                    ref="vtk_view",
                    picking_modes=("['click']",),
                    click=(on_click, "[$event]"),
                ) as view:
                    _get_scene_object_id = view.get_scene_object_id
                server.controller.view_update = view.update
                server.controller.view_reset_camera = view.reset_camera
                # Reset view button (bottom-left)
                with v3.VBtn(
                    icon=True,
                    variant="flat",
                    size="small",
                    color="grey-lighten-1",
                    click=(reset_view, "[]"),
                    style=(
                        "position: absolute; bottom: 8px; left: 8px;"
                        " min-width: 32px; width: 32px; height: 32px;"
                        " opacity: 0.7; z-index: 1;"
                    ),
                    classes="reset-view-btn",
                ):
                    v3.VIcon("mdi-fit-to-screen-outline", size="small")
                # Text overlay showing selected object name
                html_widgets.Div(
                    "{{ selected_object }}",
                    v_show="selected_object",
                    style=(
                        "position: absolute; bottom: 8px; left: 50%;"
                        " transform: translateX(-50%);"
                        " background: rgba(0,0,0,0.65); color: #fff;"
                        " padding: 4px 14px; border-radius: 4px;"
                        " font-size: 13px; pointer-events: none;"
                        " white-space: nowrap;"
                    ),
                )
    else:
        with v3.VCard(
            classes="fill-height d-flex align-center justify-center",
            flat=True,
            rounded=0,
            color="grey-darken-3",
        ):
            html_widgets.Div(
                "3D Viewport (VTK not available)",
                style="color: #aaa; font-size: 14px;",
            )
