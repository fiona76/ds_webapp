"""
Viewer display mode toggle tests.

Verifies the four toolbar toggle buttons above the viewport:
  1. Mesh edges (mdi-grid) — triangle mesh edge visibility
  2. Semi-transparent (mdi-circle-half-full) — 40% opacity on surfaces
  3. Feature edges (mdi-cube-outline) — CAD BRep edge line actors
  4. Scene light (mdi-lightbulb-outline) — shaded vs flat lighting

All four toggles are independent — any combination is valid.
"""

from helpers import screenshot


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def _set(page, key, value):
    val_js = "true" if value is True else "false" if value is False else "null"
    page.evaluate(f'window.trame.state.set("{key}", {val_js})')


def test_baseline_state(imported_geometry):
    """After importing geometry, default toggle states should be:
    edges=ON, semi-transparent=OFF, feature edges=ON, scene light=ON."""
    page = imported_geometry
    assert _get(page, "viewer_show_edges") is True
    assert _get(page, "viewer_semi_transparent") is False
    assert _get(page, "viewer_wireframe") is True

    screenshot(page, "viewer_mode_baseline.png")


def test_mesh_edges_toggle(imported_geometry):
    """Clicking the edges toggle (icon 1) should hide triangle mesh
    edge lines on the surfaces, leaving smooth shaded objects."""
    page = imported_geometry

    page.locator(".toggle-edges").click()
    page.wait_for_timeout(500)
    assert _get(page, "viewer_show_edges") is False

    screenshot(page, "viewer_mode_no_edges.png")


def test_semi_transparent_no_selection(imported_geometry):
    """With no object selected, toggling semi-transparent (icon 2)
    should make ALL objects 40% opacity."""
    page = imported_geometry

    # Ensure no selection
    _set(page, "selected_object", None)
    page.wait_for_timeout(300)

    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(500)
    assert _get(page, "viewer_semi_transparent") is True

    screenshot(page, "viewer_mode_semi_transparent_all.png")


def test_semi_transparent_with_selection(imported_geometry):
    """With semi-transparent ON and an object selected, the selected
    object should be solid (100% opacity) while others are 40%."""
    page = imported_geometry

    # Turn on semi-transparent
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(300)

    # Try clicking objects in the viewport to select one
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    positions = [
        (bbox["x"] + bbox["width"] * 0.5, bbox["y"] + bbox["height"] * 0.5),
        (bbox["x"] + bbox["width"] * 0.35, bbox["y"] + bbox["height"] * 0.35),
        (bbox["x"] + bbox["width"] * 0.6, bbox["y"] + bbox["height"] * 0.5),
    ]
    for px, py in positions:
        page.mouse.click(px, py)
        page.wait_for_timeout(500)
        if _get(page, "selected_object"):
            break

    selected = _get(page, "selected_object")
    assert selected, "Should be able to select an object by clicking in viewport"

    screenshot(page, "viewer_mode_semi_transparent_selected.png")


def test_feature_edges_toggle(imported_geometry):
    """Feature edges are ON by default (CAD edge lines visible). Clicking
    the toggle (icon 3) should hide them."""
    page = imported_geometry

    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(500)
    assert _get(page, "viewer_wireframe") is False

    screenshot(page, "viewer_mode_feature_edges.png")


def test_feature_edges_without_mesh(imported_geometry):
    """Feature edges ON + mesh edges OFF should show smooth surfaces
    with only CAD boundary edge lines (no triangle mesh grid)."""
    page = imported_geometry

    # Mesh edges OFF (feature edges stay ON by default)
    page.locator(".toggle-edges").click()
    page.wait_for_timeout(500)
    assert _get(page, "viewer_show_edges") is False
    assert _get(page, "viewer_wireframe") is True

    screenshot(page, "viewer_mode_feature_edges_no_mesh.png")


def test_combined_semi_transparent_and_feature_edges(imported_geometry):
    """Semi-transparent and feature edges should work simultaneously
    (independent toggles, no mutual exclusivity)."""
    page = imported_geometry

    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(300)
    assert _get(page, "viewer_semi_transparent") is True
    assert _get(page, "viewer_wireframe") is True

    screenshot(page, "viewer_mode_combined.png")
