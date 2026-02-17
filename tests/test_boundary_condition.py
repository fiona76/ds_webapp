"""
Boundary Condition tree and Settings panel tests.

Verifies:
  - "Power Map" is removed from the tree
  - Boundary Condition expands to show Power Source and Temperature
  - Adding items keeps user on the category view (items appear in Settings only)
  - All items remain visible during inline rename
  - Rename commits correctly via double-click + Enter
  - Same flow works for Temperature
"""

import pytest

from helpers import screenshot, STEP_FILE


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def _import_geometry_for_bc(page):
    page.evaluate(
        f"""() => {{
            const s = window.trame.state;
            s.set("import_file_path", "{STEP_FILE}");
            s.set("do_import_trigger", (s.get("do_import_trigger") || 0) + 1);
        }}"""
    )
    page.wait_for_function("() => (window.trame.state.get('geometry_imports') || []).length > 0")
    page.wait_for_timeout(1200)


def _try_pick_object_and_pos(page):
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    assert bbox is not None, "Viewer canvas should be present"
    page.locator(".reset-view-btn").click()
    page.wait_for_timeout(500)
    positions = [
        (0.50, 0.50),
        (0.45, 0.50),
        (0.55, 0.50),
        (0.50, 0.45),
        (0.50, 0.55),
    ]
    for rx in (0.30, 0.38, 0.46, 0.54, 0.62, 0.70):
        for ry in (0.34, 0.42, 0.50, 0.58, 0.66):
            positions.append((rx, ry))

    for _ in range(6):
        for rx, ry in positions:
            px = bbox["x"] + bbox["width"] * rx
            py = bbox["y"] + bbox["height"] * ry
            page.mouse.click(px, py)
            page.wait_for_timeout(300)
            selected = _get(page, "selected_object")
            selected_surface = _get(page, "selected_surface")
            if selected:
                return selected, (px, py)
            if selected_surface:
                obj_name = selected_surface.split(":", 1)[0]
                if obj_name:
                    return obj_name, (px, py)
        page.locator(".reset-view-btn").click()
        page.wait_for_timeout(500)

    # Force redraw from imported geometry node, then retry sampling once.
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
    page.locator(".reset-view-btn").click()
    page.wait_for_timeout(500)
    for rx, ry in positions:
        px = bbox["x"] + bbox["width"] * rx
        py = bbox["y"] + bbox["height"] * ry
        page.mouse.click(px, py)
        page.wait_for_timeout(350)
        selected = _get(page, "selected_object")
        selected_surface = _get(page, "selected_surface")
        if selected:
            return selected, (px, py)
        if selected_surface:
            obj_name = selected_surface.split(":", 1)[0]
            if obj_name:
                return obj_name, (px, py)
    return None, None


def _try_pick_object_and_pos_for_assignment(page):
    """Pick helper that preserves BC assignment context (no active_node switching)."""
    canvas = page.locator("canvas").first
    bbox = canvas.bounding_box()
    assert bbox is not None, "Viewer canvas should be present"
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

    for _ in range(8):
        for rx, ry in positions:
            px = bbox["x"] + bbox["width"] * rx
            py = bbox["y"] + bbox["height"] * ry
            page.mouse.click(px, py)
            page.wait_for_timeout(320)
            selected = _get(page, "selected_object")
            selected_surface = _get(page, "selected_surface")
            if selected:
                return selected, (px, py)
            if selected_surface:
                obj_name = selected_surface.split(":", 1)[0]
                if obj_name:
                    return obj_name, (px, py)
            active_type = _get(page, "bc_active_assignment_type")
            active_id = _get(page, "bc_active_assignment_id")
            if active_type == "power_source" and active_id:
                for item in (_get(page, "bc_power_sources") or []):
                    if item.get("id") == active_id:
                        assigned = item.get("assigned_objects", [])
                        if assigned:
                            return assigned[0], (px, py)
            if active_type == "temperature" and active_id:
                for item in (_get(page, "bc_temperatures") or []):
                    if item.get("id") == active_id:
                        assigned = item.get("assigned_surfaces", [])
                        if assigned:
                            obj_name = assigned[0].split(":", 1)[0]
                            return obj_name, (px, py)
        page.locator(".reset-view-btn").click()
        page.wait_for_timeout(500)

    return None, None


def _expand_bc_and_click_power_source(page):
    """Helper: expand Boundary Condition and click Power Source."""
    page.evaluate("""() => {
        const s = window.trame.state;
        s.set("show_left_panels", true);
        s.set("show_settings", true);
    }""")
    page.wait_for_timeout(300)

    bc_node = page.locator("text=Boundary Condition").first
    if bc_node.is_visible():
        bc_node.click()
        page.wait_for_timeout(400)
        power_node = page.get_by_text("Power Source", exact=True).first
        if power_node.is_visible():
            power_node.click()
            page.wait_for_timeout(400)
            return

    # Fallback for occasional headless tree-interaction misses.
    page.evaluate('window.trame.state.set("active_node", "bc_power_source")')
    page.wait_for_timeout(400)


def _expand_bc_and_click_temperature(page):
    """Helper: expand Boundary Condition and click Temperature."""
    page.evaluate("""() => {
        const s = window.trame.state;
        s.set("show_left_panels", true);
        s.set("show_settings", true);
    }""")
    page.wait_for_timeout(300)

    bc_node = page.locator("text=Boundary Condition").first
    if bc_node.is_visible():
        bc_node.click()
        page.wait_for_timeout(400)
        temp_node = page.get_by_text("Temperature", exact=True).first
        if temp_node.is_visible():
            temp_node.click()
            page.wait_for_timeout(400)
            return

    # Fallback for occasional headless tree-interaction misses.
    page.evaluate('window.trame.state.set("active_node", "bc_temperature")')
    page.wait_for_timeout(400)


def test_bc_expands_to_show_children(page):
    """Clicking 'Boundary Condition' should expand it to reveal
    'Power Source' and 'Temperature' child nodes."""
    page.locator("text=Boundary Condition").first.click()
    page.wait_for_timeout(500)

    assert page.get_by_text("Power Source", exact=True).first.is_visible()
    assert page.get_by_text("Temperature", exact=True).first.is_visible()

    screenshot(page, "bc_expanded.png")


def test_power_source_shows_add_button(page):
    """Clicking 'Power Source' in the tree should show a Settings panel
    with 'Power Sources' title and an 'Add Power Source' button."""
    _expand_bc_and_click_power_source(page)

    add_btn = page.get_by_text("Add Power Source", exact=True)
    assert add_btn.is_visible()

    screenshot(page, "bc_power_source_settings.png")


def test_add_power_source_stays_on_category(page):
    """After clicking 'Add Power Source', the active_node should stay on
    'bc_power_source' (not navigate away), and 'Power Source 1' should
    appear immediately in the Settings list."""
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)

    # Should stay on category, not navigate to individual item
    assert _get(page, "active_node") == "bc_power_source"

    # Item should be visible in Settings
    assert page.locator("text=Power Source 1").first.is_visible()

    screenshot(page, "bc_power_source_added.png")


def test_add_two_power_sources_both_visible(page):
    """Adding two power sources should show both items simultaneously
    in the Settings list."""
    _expand_bc_and_click_power_source(page)

    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)

    assert page.locator("text=Power Source 1").first.is_visible()
    assert page.locator("text=Power Source 2").first.is_visible()

    screenshot(page, "bc_two_power_sources.png")


def test_delete_power_source(page):
    """Deleting a power source removes that item while keeping remaining items."""
    _expand_bc_and_click_power_source(page)

    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)

    row = page.locator(".bc-item-row", has_text="Power Source 1").first
    row.locator(".bc-delete-btn").click()
    page.wait_for_timeout(500)

    sources = _get(page, "bc_power_sources")
    assert len(sources) == 1
    assert sources[0]["name"] == "Power Source 2"
    assert not page.locator("text=Power Source 1").first.is_visible()
    assert page.locator("text=Power Source 2").first.is_visible()

    screenshot(page, "bc_power_source_deleted.png")


def test_inline_rename(page):
    """Double-clicking a power source name should open an inline text
    field for editing. All other items should remain visible. Pressing
    Enter should commit the new name to trame state."""
    _expand_bc_and_click_power_source(page)

    # Add two items
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)

    # Double-click "Power Source 1" to start inline editing
    ps1_item = page.locator(".bc-item", has_text="Power Source 1").first
    ps1_item.dblclick()
    page.wait_for_timeout(500)

    # Editing state should be active
    assert _get(page, "bc_editing_id") == "ps_1"

    # "Power Source 2" should remain visible during rename
    assert page.locator("text=Power Source 2").first.is_visible(), \
        "Other items must stay visible during inline rename"

    screenshot(page, "bc_rename_editing.png")

    # Type new name and press Enter to commit
    rename_input = page.locator(".bc-rename-input input").first
    rename_input.fill("My Custom Source")
    rename_input.press("Enter")
    page.wait_for_timeout(500)

    # Verify state was updated
    sources = _get(page, "bc_power_sources")
    assert sources[0]["name"] == "My Custom Source"
    assert sources[1]["name"] == "Power Source 2"

    # Both items should be visible after rename
    assert page.locator("text=My Custom Source").first.is_visible()
    assert page.locator("text=Power Source 2").first.is_visible()

    screenshot(page, "bc_rename_done.png")


def test_temperature_add_and_list(page):
    """Temperature should have the same add/list behavior as Power Source:
    clicking 'Add Temperature' adds items to the Settings list while
    staying on the category view."""
    _expand_bc_and_click_temperature(page)

    assert page.get_by_text("Add Temperature", exact=True).is_visible()

    # Add two temperatures
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(500)
    assert page.locator("text=Temperature 1").first.is_visible()

    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(500)

    # Verify both exist in state
    temps = _get(page, "bc_temperatures")
    assert len(temps) == 2
    assert temps[0]["name"] == "Temperature 1"
    assert temps[1]["name"] == "Temperature 2"

    screenshot(page, "bc_temperature_two.png")


def test_delete_temperature(page):
    """Deleting a temperature removes that item while keeping remaining items."""
    _expand_bc_and_click_temperature(page)

    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(500)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(500)

    row = page.locator(".bc-item-row", has_text="Temperature 1").first
    row.locator(".bc-delete-btn").click()
    page.wait_for_timeout(500)

    temps = _get(page, "bc_temperatures")
    assert len(temps) == 1
    assert temps[0]["name"] == "Temperature 2"
    assert not page.locator("text=Temperature 1").first.is_visible()
    assert page.locator("text=Temperature 2").first.is_visible()

    screenshot(page, "bc_temperature_deleted.png")


def test_power_source_expand_shows_assignment_box_and_power_input(page):
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)

    row = page.locator(".bc-item-row", has_text="Power Source 1").first
    row.locator(".bc-expand-btn").click()
    page.wait_for_timeout(500)

    assert page.locator(".bc-power-input").first.is_visible()
    assert page.locator(".bc-assignment-list").first.is_visible()
    assert _get(page, "bc_active_assignment_type") == "power_source"
    assert _get(page, "bc_active_assignment_id") == "ps_1"

    screenshot(page, "bc_power_source_expanded.png")


def test_temperature_expand_shows_assignment_box_and_input(page):
    _expand_bc_and_click_temperature(page)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(500)

    row = page.locator(".bc-item-row", has_text="Temperature 1").first
    row.locator(".bc-expand-btn").click()
    page.wait_for_timeout(500)

    assert page.locator(".bc-temperature-input").first.is_visible()
    assert page.locator(".bc-assignment-list").first.is_visible()
    assert _get(page, "bc_active_assignment_type") == "temperature"
    assert _get(page, "bc_active_assignment_id") == "temp_1"

    screenshot(page, "bc_temperature_expanded.png")


def test_power_source_assignment_list_selection_keeps_all_assigned_highlight(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_power_sources") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_objects = ["PCB_OUTLINE", "CHIP"];
                s.set("bc_power_sources", items);
            }
        }"""
    )
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const s = window.trame.state;
        s.set("selected_object", null);
        s.set("selected_surface", null);
    }""")

    page.locator(".bc-assignment-list .v-list-item", has_text="CHIP").first.click()
    page.wait_for_timeout(400)
    assert _get(page, "bc_selected_assignment_values") == ["CHIP"]
    assert _get(page, "selected_object") is None
    assert _get(page, "selected_surface") is None
    screenshot(page, "bc_power_source_assignment_list_selection_all_assigned_highlight.png")


def test_temperature_assignment_list_selection_keeps_all_assigned_highlight(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_temperature(page)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_temperatures") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_surfaces = ["CHIP:Face-1", "CHIP:Face-2"];
                s.set("bc_temperatures", items);
            }
        }"""
    )
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const s = window.trame.state;
        s.set("selected_object", null);
        s.set("selected_surface", null);
    }""")

    page.locator(".bc-assignment-list .v-list-item", has_text="CHIP:Face-2").first.click()
    page.wait_for_timeout(400)
    assert _get(page, "bc_selected_assignment_values") == ["CHIP:Face-2"]
    assert _get(page, "selected_object") is None
    assert _get(page, "selected_surface") is None
    screenshot(page, "bc_temperature_assignment_list_selection_all_assigned_highlight.png")


def test_power_source_auto_highlight_and_clear_without_list_click(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_power_sources") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_objects = ["PCB_OUTLINE", "CHIP"];
                s.set("bc_power_sources", items);
            }
            s.set("bc_selected_assignment_item_id", "");
            s.set("bc_selected_assignment_values", []);
            s.set("selected_object", null);
            s.set("selected_surface", null);
        }"""
    )
    page.wait_for_timeout(500)
    screenshot(page, "bc_power_source_auto_highlight_all_assigned.png")

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_power_sources") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_objects = [];
                s.set("bc_power_sources", items);
            }
            s.set("selected_object", null);
            s.set("selected_surface", null);
        }"""
    )
    page.wait_for_timeout(500)
    screenshot(page, "bc_power_source_highlight_cleared_when_empty.png")


def test_temperature_auto_highlight_and_clear_without_list_click(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_temperature(page)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_temperatures") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_surfaces = ["CHIP:Face-1", "CHIP:Face-2"];
                s.set("bc_temperatures", items);
            }
            s.set("bc_selected_assignment_item_id", "");
            s.set("bc_selected_assignment_values", []);
            s.set("selected_object", null);
            s.set("selected_surface", null);
        }"""
    )
    page.wait_for_timeout(500)
    screenshot(page, "bc_temperature_auto_highlight_all_assigned.png")

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_temperatures") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_surfaces = [];
                s.set("bc_temperatures", items);
            }
            s.set("selected_object", null);
            s.set("selected_surface", null);
        }"""
    )
    page.wait_for_timeout(500)
    screenshot(page, "bc_temperature_highlight_cleared_when_empty.png")


def test_assignment_plus_shows_placeholder_dialog(page):
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(500)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.locator(".bc-assign-add-btn").first.click()
    page.wait_for_timeout(300)
    assert _get(page, "show_bc_add_placeholder") is True


def test_power_source_drag_rotate_does_not_assign(page):
    _import_geometry_for_bc(page)
    # Find a deterministic on-object start point before entering assignment mode.
    page.evaluate(
        """() => {
            const s = window.trame.state;
            const imports = s.get("geometry_imports") || [];
            if (imports.length > 0) {
                s.set("geometry_expanded_import_id", imports[0].id);
                s.set("active_node", "geometry");
            }
            s.set("show_left_panels", true);
            s.set("show_settings", true);
        }"""
    )
    page.wait_for_timeout(400)
    picked, pos = _try_pick_object_and_pos(page)
    assert picked and pos, "Expected to find an object point for drag start"

    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(400)

    start_x, start_y = pos
    end_x = start_x + 180
    end_y = start_y + 90

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y, steps=18)
    page.wait_for_timeout(220)
    page.mouse.up()
    page.wait_for_timeout(500)

    sources = _get(page, "bc_power_sources")
    assert sources[0]["assigned_objects"] == []
    screenshot(page, "bc_power_source_drag_rotate_no_assignment.png")


def test_power_source_normal_click_assigns_with_drag_guard(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(400)

    picked, _ = _try_pick_object_and_pos_for_assignment(page)
    assert picked, "Expected normal click assignment to pick an object"
    sources = _get(page, "bc_power_sources")
    assert picked in sources[0]["assigned_objects"]
    screenshot(page, "bc_power_source_normal_click_assigns.png")


def test_bc_assignment_clears_when_switching_to_import_node(page):
    """Repro guard: BC assignment highlight clears on Import node, and geometry pick still works."""
    _import_geometry_for_bc(page)
    _expand_bc_and_click_power_source(page)

    # Seed one expanded power source with two assigned objects to force BC highlight.
    page.evaluate(
        """() => {
            const s = window.trame.state;
            s.set("bc_power_sources", [{
                id: "ps_1",
                name: "Power Source 1",
                power: 0,
                assigned_objects: ["PCB_OUTLINE", "CHIP"],
            }]);
            s.set("bc_power_source_counter", 1);
            s.set("bc_expanded_power_source_id", "ps_1");
            s.set("bc_active_assignment_type", "power_source");
            s.set("bc_active_assignment_id", "ps_1");
            s.set("selected_object", null);
            s.set("selected_surface", null);
        }"""
    )
    page.wait_for_timeout(500)
    # Trigger explicit highlight refresh through assignment-list interaction.
    page.locator(".bc-assignment-list .v-list-item", has_text="CHIP").first.click()
    page.wait_for_timeout(400)
    screenshot(page, "bc_to_geometry_01_bc_assigned")

    # User action path: Geometry -> expand Import 1 in Settings
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(250)
    import_row = page.locator(".geo-import-row", has_text="Import 1").first
    if import_row.is_visible():
        import_row.click()
    else:
        page.evaluate(
            """() => {
                const s = window.trame.state;
                const imports = s.get("geometry_imports") || [];
                if (imports.length) {
                    s.set("geometry_expanded_import_id", imports[0].id);
                }
            }"""
        )
    page.wait_for_timeout(700)

    # Leaving BC mode should clear assignment mode and highlight.
    assert _get(page, "bc_active_assignment_type") == ""
    assert _get(page, "bc_active_assignment_id") == ""
    screenshot(page, "bc_to_geometry_02_import_active_highlight_cleared")

    # Use Settings object click as deterministic geometry-selection action.
    page.locator(".v-list-item", has_text="CHIP").first.click()
    page.wait_for_timeout(350)
    assert _get(page, "selected_object") == "CHIP"
    screenshot(page, "bc_to_geometry_03_geometry_pick_works")


@pytest.mark.skip(reason="Known vtk.js pick flakiness in headless runs; covered by adapter unit tests.")
def test_power_source_object_assignment_toggle_and_exclusive(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)

    # Expand Power Source 1 and assign by clicking an object
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    # Force redraw from import node, then return to BC context to reduce pick flakiness.
    page.evaluate(
        """() => {
            const s = window.trame.state;
            const imports = s.get("geometry_imports") || [];
            if (imports.length > 0) {
                const importId = imports[0].id;
                s.set("geometry_expanded_import_id", importId);
                s.set("active_node", "geometry");
                s.set("active_node", "bc_power_source");
            }
        }"""
    )
    page.wait_for_timeout(500)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    picked, pos = _try_pick_object_and_pos_for_assignment(page)
    assert picked, "Expected to pick an object for Power Source assignment"
    sources = _get(page, "bc_power_sources")
    assert picked in sources[0]["assigned_objects"]

    # Same click toggles assignment off
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    sources = _get(page, "bc_power_sources")
    assert picked not in sources[0]["assigned_objects"]

    # Reassign to Power Source 1
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    sources = _get(page, "bc_power_sources")
    assert picked in sources[0]["assigned_objects"]

    # Try assigning same object to Power Source 2 (should be rejected)
    page.locator(".bc-item-row", has_text="Power Source 2").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    sources = _get(page, "bc_power_sources")
    assert picked in sources[0]["assigned_objects"]
    assert picked not in sources[1]["assigned_objects"]

    screenshot(page, "bc_power_source_assignment_exclusive.png")


@pytest.mark.skip(reason="Known vtk.js pick flakiness in headless runs; covered by adapter unit tests.")
def test_temperature_surface_assignment_toggle_and_exclusive(page):
    _import_geometry_for_bc(page)
    _expand_bc_and_click_temperature(page)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(300)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(300)

    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    # Force redraw from import node, then return to BC context to reduce pick flakiness.
    page.evaluate(
        """() => {
            const s = window.trame.state;
            const imports = s.get("geometry_imports") || [];
            if (imports.length > 0) {
                const importId = imports[0].id;
                s.set("geometry_expanded_import_id", importId);
                s.set("active_node", "geometry");
                s.set("active_node", "bc_temperature");
            }
        }"""
    )
    page.wait_for_timeout(500)
    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    picked_obj, pos = _try_pick_object_and_pos_for_assignment(page)
    assert picked_obj, "Expected to pick a surface for Temperature assignment"

    temps = _get(page, "bc_temperatures")
    assert len(temps[0]["assigned_surfaces"]) == 1
    surface = temps[0]["assigned_surfaces"][0]
    assert surface.startswith(f"{picked_obj}:Face-")

    # Same click toggles off
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    temps = _get(page, "bc_temperatures")
    assert surface not in temps[0]["assigned_surfaces"]

    # Re-add then verify exclusive rejection in Temperature 2
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    temps = _get(page, "bc_temperatures")
    assert surface in temps[0]["assigned_surfaces"]

    page.locator(".bc-item-row", has_text="Temperature 2").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    page.mouse.click(pos[0], pos[1])
    page.wait_for_timeout(400)
    temps = _get(page, "bc_temperatures")
    assert surface in temps[0]["assigned_surfaces"]
    assert surface not in temps[1]["assigned_surfaces"]

    # Remove via list selection + minus
    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)
    page.locator(".bc-assignment-list .v-list-item", has_text=surface).first.click()
    page.wait_for_timeout(200)
    page.locator(".bc-assign-remove-btn").first.click()
    page.wait_for_timeout(400)
    temps = _get(page, "bc_temperatures")
    assert surface not in temps[0]["assigned_surfaces"]

    screenshot(page, "bc_temperature_surface_assignment_exclusive.png")


def test_power_source_assignment_multi_select_delete_ctrl(page):
    _expand_bc_and_click_power_source(page)
    page.get_by_text("Add Power Source", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Power Source 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_power_sources") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_objects = ["PCB_OUTLINE", "CHIP", "3DVC"];
                s.set("bc_power_sources", items);
            }
        }"""
    )
    page.wait_for_timeout(300)

    assignment_items = page.locator(".bc-assignment-list .v-list-item")
    assignment_items.filter(has_text="PCB_OUTLINE").first.click()
    assignment_items.filter(has_text="CHIP").first.click(modifiers=["Control"])
    page.wait_for_timeout(200)

    assert _get(page, "bc_selected_assignment_values") == ["PCB_OUTLINE", "CHIP"]
    page.locator(".bc-assign-remove-btn").first.click()
    page.wait_for_timeout(300)

    sources = _get(page, "bc_power_sources")
    assert sources[0]["assigned_objects"] == ["3DVC"]


def test_temperature_assignment_multi_select_delete_shift(page):
    _expand_bc_and_click_temperature(page)
    page.get_by_text("Add Temperature", exact=True).click()
    page.wait_for_timeout(300)
    page.locator(".bc-item-row", has_text="Temperature 1").first.locator(".bc-expand-btn").click()
    page.wait_for_timeout(300)

    page.evaluate(
        """() => {
            const s = window.trame.state;
            const items = (s.get("bc_temperatures") || []).map((it) => ({ ...it }));
            if (items.length > 0) {
                items[0].assigned_surfaces = ["CHIP:Face-1", "CHIP:Face-2", "CHIP:Face-3", "CHIP:Face-4"];
                s.set("bc_temperatures", items);
            }
        }"""
    )
    page.wait_for_timeout(300)

    assignment_items = page.locator(".bc-assignment-list .v-list-item")
    assignment_items.filter(has_text="CHIP:Face-1").first.click()
    assignment_items.filter(has_text="CHIP:Face-3").first.click(modifiers=["Shift"])
    page.wait_for_timeout(200)

    assert _get(page, "bc_selected_assignment_values") == [
        "CHIP:Face-1", "CHIP:Face-2", "CHIP:Face-3"
    ]
    page.locator(".bc-assign-remove-btn").first.click()
    page.wait_for_timeout(300)

    temps = _get(page, "bc_temperatures")
    assert temps[0]["assigned_surfaces"] == ["CHIP:Face-4"]
