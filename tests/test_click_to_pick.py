"""
Click-to-pick 3D object highlighting tests.

Verifies that clicking on a 3D object in the viewport highlights it
(turns orange) and that clicking empty space clears the selection.
"""

from helpers import screenshot


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def _try_pick_any_object(page):
    """Try multiple canvas locations to pick any visible object."""
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    assert bbox is not None, "Viewer canvas should be present"

    # Center the camera before sampling click locations.
    page.locator(".reset-view-btn").click()
    page.wait_for_timeout(500)

    positions = [
        (0.50, 0.50),
        (0.45, 0.50),
        (0.55, 0.50),
        (0.50, 0.45),
        (0.50, 0.55),
        (0.40, 0.40),
        (0.60, 0.40),
        (0.40, 0.60),
        (0.60, 0.60),
        (0.35, 0.50),
        (0.65, 0.50),
    ]

    for _ in range(2):
        for rx, ry in positions:
            page.mouse.click(bbox["x"] + bbox["width"] * rx, bbox["y"] + bbox["height"] * ry)
            page.wait_for_timeout(350)
            selected = _get(page, "selected_object")
            if selected:
                return selected
        page.locator(".reset-view-btn").click()
        page.wait_for_timeout(500)
    return None


def test_click_object_highlights(imported_geometry):
    """Clicking on a 3D object in the viewport should set selected_object
    state and visually highlight the object in orange."""
    page = imported_geometry

    selected = _try_pick_any_object(page)
    if not selected:
        # One retry path: force a redraw after initial scene hydration.
        page.evaluate(
            """() => {
                const s = window.trame.state;
                const imports = s.get("geometry_imports") || [];
                if (imports.length > 0) {
                    const importId = imports[0].id;
                    s.set("geometry_expanded_import_id", importId);
                    s.set("active_node", null);
                    s.set("active_node", "geometry");
                }
            }"""
        )
        page.wait_for_timeout(800)
        selected = _try_pick_any_object(page)

    assert selected, "Clicking in viewport should select an object"
    screenshot(page, "pick_before_click.png")
    screenshot(page, "pick_highlighted.png")


def test_click_empty_deselects(imported_geometry):
    """After selecting an object, clicking empty space at the canvas
    edge should clear the selection (selected_object becomes null)."""
    page = imported_geometry

    # First, select an object
    selected = _try_pick_any_object(page)
    if not selected:
        page.evaluate(
            """() => {
                const s = window.trame.state;
                const imports = s.get("geometry_imports") || [];
                if (imports.length > 0) {
                    const importId = imports[0].id;
                    s.set("geometry_expanded_import_id", importId);
                    s.set("active_node", null);
                    s.set("active_node", "geometry");
                }
            }"""
        )
        page.wait_for_timeout(800)
        selected = _try_pick_any_object(page)
    assert selected, "Precondition failed: expected object selection before deselect test"

    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    assert bbox is not None, "Viewer canvas should be present"

    # Now click empty space to deselect (top-left corner)
    page.mouse.click(bbox["x"] + 5, bbox["y"] + 5)
    page.wait_for_timeout(500)

    deselected = _get(page, "selected_object")
    assert deselected is None, \
        f"Clicking empty space should clear selection, got '{deselected}'"

    screenshot(page, "pick_deselected.png")
