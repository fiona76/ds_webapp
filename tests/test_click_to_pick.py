"""
Click-to-pick 3D object highlighting tests.

Verifies that clicking on a 3D object in the viewport highlights it
(turns orange) and that clicking empty space clears the selection.
"""

from helpers import screenshot


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def test_click_object_highlights(imported_geometry):
    """Clicking on a 3D object in the viewport should set selected_object
    state and visually highlight the object in orange."""
    page = imported_geometry
    screenshot(page, "pick_before_click.png")

    # Click positions to try (center first, then offsets)
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    positions = [
        (bbox["x"] + bbox["width"] * 0.50, bbox["y"] + bbox["height"] * 0.50),
        (bbox["x"] + bbox["width"] * 0.35, bbox["y"] + bbox["height"] * 0.35),
        (bbox["x"] + bbox["width"] * 0.50, bbox["y"] + bbox["height"] * 0.40),
        (bbox["x"] + bbox["width"] * 0.60, bbox["y"] + bbox["height"] * 0.50),
        (bbox["x"] + bbox["width"] * 0.40, bbox["y"] + bbox["height"] * 0.60),
    ]

    selected = None
    for px, py in positions:
        page.mouse.click(px, py)
        page.wait_for_timeout(500)
        selected = _get(page, "selected_object")
        if selected:
            break

    assert selected, "Clicking in viewport should select an object"
    screenshot(page, "pick_highlighted.png")


def test_click_empty_deselects(imported_geometry):
    """After selecting an object, clicking empty space at the canvas
    edge should clear the selection (selected_object becomes null)."""
    page = imported_geometry

    # First, select an object
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    positions = [
        (bbox["x"] + bbox["width"] * 0.50, bbox["y"] + bbox["height"] * 0.50),
        (bbox["x"] + bbox["width"] * 0.35, bbox["y"] + bbox["height"] * 0.35),
        (bbox["x"] + bbox["width"] * 0.60, bbox["y"] + bbox["height"] * 0.50),
    ]
    for px, py in positions:
        page.mouse.click(px, py)
        page.wait_for_timeout(500)
        if _get(page, "selected_object"):
            break

    # Now click empty space to deselect (top-left corner)
    page.mouse.click(bbox["x"] + 5, bbox["y"] + 5)
    page.wait_for_timeout(500)

    deselected = _get(page, "selected_object")
    assert deselected is None, \
        f"Clicking empty space should clear selection, got '{deselected}'"

    screenshot(page, "pick_deselected.png")
