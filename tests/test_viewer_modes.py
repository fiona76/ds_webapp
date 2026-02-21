"""
Viewer display mode toggle tests.

Toolbar buttons (after refactor):
  B — Semi-transparent (mdi-circle-half-full) : viewer_semi_transparent, 40% opacity
  C — Wireframe-only  (mdi-cube-outline)      : viewer_wireframe_only, opacity=0 (edge lines only)
  D — Scene light     (mdi-lightbulb-outline) : viewer_scene_light

Removed:
  A — Mesh edges removed; viewer_show_edges hard-defaults to False, no button.

Mutual exclusivity: B and C cannot both be on at the same time.

Wireframe mode (viewer_wireframe) is always True; no toolbar button.
"""

from helpers import screenshot


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def _set(page, key, value):
    if value is True:
        val_js = "true"
    elif value is False:
        val_js = "false"
    elif value is None:
        val_js = "null"
    else:
        val_js = repr(value)
    page.evaluate(f'window.trame.state.set("{key}", {val_js})')


def _select_first_object_via_state(page):
    """Select the first geometry object by setting state directly (simulates tree click).
    geometry_imports[i].objects is a list of name strings, not dicts."""
    page.evaluate("""() => {
        const s = window.trame.state;
        const imports = s.get("geometry_imports") || [];
        if (imports.length === 0) return;
        const objs = imports[0].objects || [];
        if (objs.length === 0) return;
        s.set("selected_object", objs[0]);
    }""")
    page.wait_for_timeout(400)


def _try_pick_viewport(page):
    """Click multiple canvas locations; return selected_object if any hit, else None."""
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    if bbox is None:
        return None
    page.locator(".reset-view-btn").click()
    page.wait_for_timeout(400)
    positions = [
        (0.50, 0.50), (0.45, 0.50), (0.55, 0.50),
        (0.50, 0.45), (0.50, 0.55),
        (0.40, 0.40), (0.60, 0.40), (0.40, 0.60), (0.60, 0.60),
        (0.35, 0.50), (0.65, 0.50),
    ]
    for rx, ry in positions:
        page.mouse.click(bbox["x"] + bbox["width"] * rx, bbox["y"] + bbox["height"] * ry)
        page.wait_for_timeout(300)
        selected = _get(page, "selected_object")
        if selected:
            return selected
    return None


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

def test_baseline_state(imported_geometry):
    """Default viewer state after geometry import:
    - viewer_show_edges: False (mesh edges always hidden, no button)
    - viewer_semi_transparent: False
    - viewer_wireframe: True (CAD feature edges always on, no button)
    - viewer_wireframe_only: False
    - viewer_scene_light: True
    """
    page = imported_geometry
    assert _get(page, "viewer_show_edges") is False
    assert _get(page, "viewer_semi_transparent") is False
    assert _get(page, "viewer_wireframe") is True
    assert _get(page, "viewer_wireframe_only") is False
    assert _get(page, "viewer_scene_light") is True
    screenshot(page, "viewer_baseline.png")


# ---------------------------------------------------------------------------
# B — Semi-transparent
# ---------------------------------------------------------------------------

def test_semi_transparent_toggle(imported_geometry):
    """Clicking B turns semi-transparent on; clicking again turns it off."""
    page = imported_geometry
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_semi_transparent") is True
    screenshot(page, "viewer_semi_transparent_on.png")

    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_semi_transparent") is False
    screenshot(page, "viewer_semi_transparent_off.png")


def test_semi_transparent_with_selection(imported_geometry):
    """B on + object selected: selected object is semi-transparent orange (0.4 opacity),
    all other objects are semi-transparent blue (0.4 opacity)."""
    page = imported_geometry
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(300)

    selected = _try_pick_viewport(page)
    assert selected, "Should be able to pick an object in viewport with B on"
    assert _get(page, "viewer_semi_transparent") is True
    screenshot(page, "viewer_semi_transparent_selected.png")


# ---------------------------------------------------------------------------
# C — Wireframe-only
# ---------------------------------------------------------------------------

def test_wireframe_only_toggle(imported_geometry):
    """Clicking C turns viewer_wireframe_only on; clicking again turns it off."""
    page = imported_geometry
    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_wireframe_only") is True
    screenshot(page, "viewer_wireframe_only_on.png")

    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_wireframe_only") is False
    screenshot(page, "viewer_wireframe_only_off.png")


def test_wireframe_only_viewport_click_selects(imported_geometry):
    """With C on, clicking the viewport must still select objects.
    The selected object should appear as semi-transparent orange (opacity=0.4)
    while unselected objects remain invisible (opacity=0)."""
    page = imported_geometry

    _set(page, "selected_object", None)
    page.wait_for_timeout(200)

    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_wireframe_only") is True

    selected = _try_pick_viewport(page)
    assert selected, (
        "Viewport click must select an object in wireframe-only mode"
    )
    screenshot(page, "viewer_wireframe_only_viewport_selected.png")


def test_wireframe_only_tree_selection_updates_state(imported_geometry):
    """With C on, selecting an object via the model tree (state set) must
    update selected_object and render it as semi-transparent orange."""
    page = imported_geometry

    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_wireframe_only") is True

    _select_first_object_via_state(page)
    selected = _get(page, "selected_object")
    assert selected, "Tree selection should set selected_object in wireframe-only mode"
    assert _get(page, "viewer_wireframe") is True  # always on

    screenshot(page, "viewer_wireframe_only_tree_selected.png")


def test_wireframe_only_selected_object_highlight(imported_geometry):
    """With C on and an object selected:
    - selected_object state is set
    - viewer_wireframe_only is still True
    - screenshot should show selected object as semi-transparent orange,
      all others invisible (only wireframe edge lines visible)

    Compare with viewer_semi_transparent_selected.png — the selected object
    colour should look the same (orange), others should be fully invisible
    instead of 40% blue."""
    page = imported_geometry

    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)

    # Select via viewport click
    selected = _try_pick_viewport(page)
    if not selected:
        # Fallback: select via state (tree selection path)
        _select_first_object_via_state(page)
        selected = _get(page, "selected_object")

    assert selected, "An object must be selected for this test"
    assert _get(page, "viewer_wireframe_only") is True

    page.wait_for_timeout(500)
    screenshot(page, "viewer_wireframe_only_highlight.png")


# ---------------------------------------------------------------------------
# Mutual exclusivity: B and C cannot both be on
# ---------------------------------------------------------------------------

def test_turning_on_C_disables_B(imported_geometry):
    """If B (semi-transparent) is on and user clicks C (wireframe-only),
    B must turn off automatically."""
    page = imported_geometry

    # Turn B on
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(300)
    assert _get(page, "viewer_semi_transparent") is True

    # Turn C on — B must turn off
    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_wireframe_only") is True, "C should be on"
    assert _get(page, "viewer_semi_transparent") is False, "B must turn off when C turns on"

    screenshot(page, "viewer_mutual_exclusion_C_disables_B.png")


def test_turning_on_B_disables_C(imported_geometry):
    """If C (wireframe-only) is on and user clicks B (semi-transparent),
    C must turn off automatically."""
    page = imported_geometry

    # Turn C on
    page.locator(".toggle-wireframe").click()
    page.wait_for_timeout(300)
    assert _get(page, "viewer_wireframe_only") is True

    # Turn B on — C must turn off
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_semi_transparent") is True, "B should be on"
    assert _get(page, "viewer_wireframe_only") is False, "C must turn off when B turns on"

    screenshot(page, "viewer_mutual_exclusion_B_disables_C.png")


def test_both_off_is_valid(imported_geometry):
    """Turning off the active button (B or C) while the other is already off
    is valid — both can be off simultaneously."""
    page = imported_geometry

    # Turn B on then off
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(200)
    page.locator(".toggle-semi-transparent").click()
    page.wait_for_timeout(400)

    assert _get(page, "viewer_semi_transparent") is False
    assert _get(page, "viewer_wireframe_only") is False
    screenshot(page, "viewer_both_off.png")


# ---------------------------------------------------------------------------
# Ruler button — position and toggle
# ---------------------------------------------------------------------------

def test_ruler_button_exists(page):
    """The ruler button (.toggle-rulers) must be present in the toolbar."""
    assert page.locator(".toggle-rulers").is_visible(), \
        "Ruler button must be visible in the toolbar"


def test_ruler_button_left_of_semi_transparent(page):
    """The ruler button must appear to the LEFT of the semi-transparent button."""
    ruler_box = page.locator(".toggle-rulers").bounding_box()
    semi_box = page.locator(".toggle-semi-transparent").bounding_box()
    assert ruler_box is not None, "Ruler button must be present"
    assert semi_box is not None, "Semi-transparent button must be present"
    assert ruler_box["x"] < semi_box["x"], (
        f"Ruler button (x={ruler_box['x']:.0f}) must be left of "
        f"semi-transparent button (x={semi_box['x']:.0f})"
    )


def test_ruler_button_toggles_state(page):
    """Clicking the ruler button must toggle viewer_show_rulers."""
    assert _get(page, "viewer_show_rulers") is False
    page.locator(".toggle-rulers").click()
    page.wait_for_timeout(300)
    assert _get(page, "viewer_show_rulers") is True
    page.locator(".toggle-rulers").click()
    page.wait_for_timeout(300)
    assert _get(page, "viewer_show_rulers") is False


# ---------------------------------------------------------------------------
# D — Scene light (unchanged, quick sanity)
# ---------------------------------------------------------------------------

def test_scene_light_toggle(imported_geometry):
    """D (scene light) is independent of B and C."""
    page = imported_geometry

    page.locator(".toggle-scene-light").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_scene_light") is False
    screenshot(page, "viewer_scene_light_off.png")

    page.locator(".toggle-scene-light").click()
    page.wait_for_timeout(400)
    assert _get(page, "viewer_scene_light") is True
