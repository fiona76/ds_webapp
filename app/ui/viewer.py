import asyncio

from trame.widgets import vuetify3 as v3, html as html_widgets

try:
    from trame.widgets import vtk as vtk_widgets
    from vtkmodules.vtkRenderingCore import (
        vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor,
        vtkPolyDataMapper, vtkActor, vtkCellPicker,
    )
    from vtkmodules.vtkCommonCore import vtkPoints
    from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray, vtkTriangle, vtkLine
    from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
    from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
    from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
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

        # Per-object surface actors: {name: [vtkActor, ...]}
        current_actors = {}
        # Per-object feature edge actors: {name: vtkActor}
        edge_actors = {}
        # Track which object list is currently displayed (by id(list))
        # to skip redundant show_geometry calls that would destroy and
        # recreate identical actors, causing VtkLocalView serializer
        # cache aliasing issues.
        _displayed_objects_id = [None]
        # Reverse mapping: {scene_object_id: object_name} for click-to-pick
        actor_id_to_name = {}
        # Reverse mapping: {scene_object_id: "Object:Face-N"} for surface assignment
        actor_id_to_surface = {}
        # Reverse mapping by actor object for picker fallback
        actor_obj_to_name = {}
        actor_obj_to_surface = {}
        object_centroids = {}    # {object_name: (x, y, z)}
        face_centroids = []      # [{"object_name", "surface_name", "centroid"}]
        pick_distance_threshold = 0.0
        # Will be set once VtkLocalView is created
        _get_scene_object_id = None
        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)

        # Initialize viewer display mode defaults
        state.viewer_show_edges = False
        state.viewer_semi_transparent = False
        state.viewer_wireframe = True
        state.viewer_wireframe_only = False
        state.viewer_scene_light = True
        state.viewer_show_rulers = False

        # Cube axes actor (rulers) — hidden until toggled on
        cube_axes = vtkCubeAxesActor()
        cube_axes.SetCamera(renderer.GetActiveCamera())
        cube_axes.SetFlyModeToClosestTriad()
        cube_axes.SetVisibility(False)
        cube_axes.SetXLabelFormat("%-#6.3g")
        cube_axes.SetYLabelFormat("%-#6.3g")
        cube_axes.SetZLabelFormat("%-#6.3g")
        cube_axes.SetXTitle("X")
        cube_axes.SetYTitle("Y")
        cube_axes.SetZTitle("Z")
        for i in range(3):
            cube_axes.GetTitleTextProperty(i).SetColor(0.2, 0.2, 0.2)
            cube_axes.GetTitleTextProperty(i).SetFontSize(12)
            cube_axes.GetLabelTextProperty(i).SetColor(0.2, 0.2, 0.2)
            cube_axes.GetLabelTextProperty(i).SetFontSize(10)
            cube_axes.GetXAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
            cube_axes.GetYAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
            cube_axes.GetZAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
        renderer.AddActor(cube_axes)

        def _style_actor(actor, highlighted=False, show_edges=True,
                         semi_transparent=False, scene_light=True, wireframe_only=False):
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
            if wireframe_only:
                # 0.001 is visually invisible but keeps the actor pickable in vtk.js.
                # opacity=0.0 causes vtk.js to skip the actor entirely during picking,
                # breaking all three pick paths in on_click.
                opacity = 0.4 if highlighted else 0.001
            else:
                opacity = 0.4 if semi_transparent else 1.0
            prop.SetOpacity(opacity)
            if scene_light:
                prop.SetAmbient(0.2)
                prop.SetDiffuse(0.8)
            else:
                prop.SetAmbient(1.0)
                prop.SetDiffuse(0.0)

        def show_geometry(objects):
            """Display geometry objects in the viewport, one actor per object."""
            # Skip rebuild if the exact same object list is already displayed.
            # Recreating actors for identical data causes VtkLocalView's delta
            # serializer to produce empty deltas (C++ memory address aliasing
            # in PROP_CACHE), which silently drops subsequent property updates.
            obj_id = id(objects) if objects else None
            if obj_id is not None and obj_id == _displayed_objects_id[0] and current_actors:
                # Same geometry already shown — just restyle and push
                _apply_all_styles()
                return
            _displayed_objects_id[0] = obj_id

            # Remove all previous actors
            for actor_list in current_actors.values():
                for actor in actor_list:
                    renderer.RemoveActor(actor)
            current_actors.clear()
            for actor in edge_actors.values():
                renderer.RemoveActor(actor)
            edge_actors.clear()
            actor_id_to_name.clear()
            actor_id_to_surface.clear()
            actor_obj_to_name.clear()
            actor_obj_to_surface.clear()
            object_centroids.clear()
            face_centroids.clear()
            all_points = []

            if not objects:
                server.controller.view_update()
                return

            for obj in objects:
                # One surface actor per CAD face (deterministic face IDs)
                face_actors = []
                faces = obj.get("faces", [])
                if not faces:
                    faces = [{
                        "face_index": 1,
                        "label": "Face-1",
                        "vertices": obj["vertices"],
                        "triangles": obj["triangles"],
                    }]
                for face in faces:
                    f_vertices = face.get("vertices", [])
                    if not f_vertices:
                        continue
                    polydata = _object_to_vtk_polydata(face)
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
                    face_actors.append(actor)

                    if _get_scene_object_id is not None:
                        surface_label = f"{obj['name']}:{face.get('label', 'Face-1')}"
                        try:
                            scene_id = _get_scene_object_id(actor)
                        except Exception:
                            scene_id = None
                        if scene_id:
                            actor_id_to_name[scene_id] = obj["name"]
                            actor_id_to_surface[scene_id] = surface_label
                    actor_obj_to_name[actor] = obj["name"]
                    actor_obj_to_surface[actor] = f"{obj['name']}:{face.get('label', 'Face-1')}"
                    cx = sum(v[0] for v in f_vertices) / len(f_vertices)
                    cy = sum(v[1] for v in f_vertices) / len(f_vertices)
                    cz = sum(v[2] for v in f_vertices) / len(f_vertices)
                    face_centroids.append({
                        "object_name": obj["name"],
                        "surface_name": f"{obj['name']}:{face.get('label', 'Face-1')}",
                        "centroid": (cx, cy, cz),
                    })
                    all_points.extend(f_vertices)
                current_actors[obj["name"]] = face_actors
                if obj.get("vertices"):
                    ov = obj["vertices"]
                    object_centroids[obj["name"]] = (
                        sum(v[0] for v in ov) / len(ov),
                        sum(v[1] for v in ov) / len(ov),
                        sum(v[2] for v in ov) / len(ov),
                    )

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
            if all_points:
                min_x = min(p[0] for p in all_points)
                max_x = max(p[0] for p in all_points)
                min_y = min(p[1] for p in all_points)
                max_y = max(p[1] for p in all_points)
                min_z = min(p[2] for p in all_points)
                max_z = max(p[2] for p in all_points)
                dx = max_x - min_x
                dy = max_y - min_y
                dz = max_z - min_z
                diag = (dx * dx + dy * dy + dz * dz) ** 0.5
                pick_distance_threshold = max(diag * 0.30, 1e-6)
                cube_axes.SetBounds(min_x, max_x, min_y, max_y, min_z, max_z)
            else:
                pick_distance_threshold = 0.0
            # Apply styles and push scene to client first.
            _apply_all_styles()
            # Then schedule a camera reset with a short delay so the client
            # finishes processing the scene update before receiving resetCamera.
            # Calling view_reset_camera() synchronously races against the scene
            # push and resets to empty bounds (wrong camera). The delay ensures
            # the client scene is ready when resetCamera arrives.
            async def _deferred_reset():
                await asyncio.sleep(0.3)
                if hasattr(server.controller, "view_reset_camera"):
                    server.controller.view_reset_camera()
            asyncio.ensure_future(_deferred_reset())

        def _apply_all_styles(*args):
            """Re-style every actor based on current selection + display mode state."""
            selected = state.selected_object
            selected_surface = state.selected_surface
            show_edges = state.viewer_show_edges
            semi_trans = state.viewer_semi_transparent
            wireframe = state.viewer_wireframe
            wireframe_only = state.viewer_wireframe_only
            scene_light = state.viewer_scene_light
            surface_mode = (
                state.bc_active_assignment_type == "temperature"
                and bool(state.bc_active_assignment_id)
            )
            power_mode = (
                state.bc_active_assignment_type == "power_source"
                and bool(state.bc_active_assignment_id)
            )
            highlighted_objects = set()
            highlighted_surfaces = set()
            if power_mode:
                for item in state.bc_power_sources:
                    if item.get("id") == state.bc_active_assignment_id:
                        highlighted_objects = set(item.get("assigned_objects", []))
                        break
            elif surface_mode:
                for item in state.bc_temperatures:
                    if item.get("id") == state.bc_active_assignment_id:
                        highlighted_surfaces = set(item.get("assigned_surfaces", []))
                        break

            for obj_name, actor_list in current_actors.items():
                for actor in actor_list:
                    if surface_mode:
                        is_highlighted = actor_obj_to_surface.get(actor) in highlighted_surfaces
                    elif power_mode:
                        is_highlighted = obj_name in highlighted_objects
                    else:
                        is_highlighted = (obj_name == selected)
                    _style_actor(
                        actor,
                        highlighted=is_highlighted,
                        show_edges=show_edges,
                        semi_transparent=semi_trans,
                        scene_light=scene_light,
                        wireframe_only=wireframe_only,
                    )

            # Toggle feature edge actors
            for obj_name, edge_actor in edge_actors.items():
                edge_actor.SetVisibility(wireframe)
                prop = edge_actor.GetProperty()
                if (not surface_mode) and (not power_mode) and obj_name == selected:
                    prop.SetColor(*EDGE_HIGHLIGHT)
                elif power_mode and obj_name in highlighted_objects:
                    prop.SetColor(*EDGE_HIGHLIGHT)
                else:
                    prop.SetColor(*EDGE_DEFAULT)

            server.controller.view_update()

        @state.change("viewer_show_edges", "viewer_semi_transparent", "viewer_wireframe", "viewer_wireframe_only", "viewer_scene_light")
        def _on_viewer_mode_change(**_):
            if current_actors:
                _apply_all_styles()

        @state.change("viewer_show_rulers", "viewer_geometry_unit")
        def _on_ruler_change(viewer_show_rulers, viewer_geometry_unit, **_):
            unit = viewer_geometry_unit or "mm"
            cube_axes.SetXTitle(f"X ({unit})")
            cube_axes.SetYTitle(f"Y ({unit})")
            cube_axes.SetZTitle(f"Z ({unit})")
            cube_axes.SetVisibility(bool(viewer_show_rulers))
            server.controller.view_update()

        def on_click(event):
            """Handle click-to-pick on the 3D viewport."""
            if event is None:
                state.selected_object = None
                state.selected_surface = None
                return
            remote_id = event.get("remoteId")
            name = actor_id_to_name.get(remote_id) if remote_id else None
            surface_name = actor_id_to_surface.get(remote_id) if remote_id else None
            if (name is None or surface_name is None) and event:
                x = y = None
                display_pos = event.get("displayPosition")
                if isinstance(display_pos, (list, tuple)) and len(display_pos) >= 2:
                    x, y = display_pos[0], display_pos[1]
                pos = event.get("position")
                if isinstance(pos, dict):
                    x = pos.get("x")
                    y = pos.get("y")
                elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    x, y = pos[0], pos[1]
                elif "x" in event and "y" in event:
                    x = event.get("x")
                    y = event.get("y")

                if x is not None and y is not None:
                    picked_actor = None
                    if picker.Pick(float(x), float(y), 0.0, renderer):
                        picked_actor = picker.GetActor()
                    if picked_actor is None:
                        rw_h = render_window.GetSize()[1]
                        if picker.Pick(float(x), float(rw_h - y), 0.0, renderer):
                            picked_actor = picker.GetActor()
                    if picked_actor is not None:
                        if name is None:
                            name = actor_obj_to_name.get(picked_actor)
                        if surface_name is None:
                            surface_name = actor_obj_to_surface.get(picked_actor)
            if (name is None or surface_name is None) and event:
                wp = event.get("worldPosition")
                if isinstance(wp, (list, tuple)) and len(wp) >= 3 and pick_distance_threshold > 0:
                    wx, wy, wz = float(wp[0]), float(wp[1]), float(wp[2])

                    best_obj_name = None
                    best_obj_dist = None
                    for obj_name, centroid in object_centroids.items():
                        dx = wx - centroid[0]
                        dy = wy - centroid[1]
                        dz = wz - centroid[2]
                        d2 = dx * dx + dy * dy + dz * dz
                        if best_obj_dist is None or d2 < best_obj_dist:
                            best_obj_dist = d2
                            best_obj_name = obj_name
                    if name is None and best_obj_name is not None and best_obj_dist is not None:
                        if (best_obj_dist ** 0.5) <= pick_distance_threshold:
                            name = best_obj_name

                    if surface_name is None and best_obj_name is not None:
                        best_surface = None
                        best_surface_dist = None
                        for face_info in face_centroids:
                            if face_info["object_name"] != best_obj_name:
                                continue
                            cx, cy, cz = face_info["centroid"]
                            dx = wx - cx
                            dy = wy - cy
                            dz = wz - cz
                            d2 = dx * dx + dy * dy + dz * dz
                            if best_surface_dist is None or d2 < best_surface_dist:
                                best_surface_dist = d2
                                best_surface = face_info["surface_name"]
                        if best_surface is not None and best_surface_dist is not None:
                            if (best_surface_dist ** 0.5) <= pick_distance_threshold:
                                surface_name = best_surface
            if state.bc_active_assignment_type == "power_source" and state.bc_active_assignment_id and name:
                if hasattr(server.controller, "toggle_assign_power_source_object"):
                    server.controller.toggle_assign_power_source_object(state.bc_active_assignment_id, name)
                state.selected_object = name
                state.selected_surface = None
            elif state.bc_active_assignment_type == "temperature" and state.bc_active_assignment_id and surface_name:
                if hasattr(server.controller, "toggle_assign_temperature_surface"):
                    server.controller.toggle_assign_temperature_surface(state.bc_active_assignment_id, surface_name)
                state.selected_object = name
                state.selected_surface = surface_name
            else:
                state.selected_object = name
                state.selected_surface = None

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
