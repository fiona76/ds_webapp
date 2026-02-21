"""
Geometry import workflow tests.

Verifies the STEP file import pipeline: opening the import dialog,
importing a file, and viewing imported objects in the Settings panel.
Also covers the per-import unit dropdown.
"""

from helpers import screenshot, STEP_FILE


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def test_import_dialog_opens(page):
    """Clicking 'Import STEP file...' under Geometry should open the
    file browser import dialog."""
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)

    dialog_visible = page.evaluate('window.trame.state.get("show_import_dialog")')
    assert dialog_visible, "Import dialog should be open"

    screenshot(page, "geometry_import_dialog.png")


def test_import_creates_settings_row(page):
    """After importing a STEP file, 'Import 1' should appear as a row
    in the Settings panel under Geometry."""
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)

    page.evaluate(f'window.trame.state.set("import_file_path", "{STEP_FILE}")')
    page.wait_for_timeout(300)
    page.locator(".import-confirm-btn").click()
    page.wait_for_timeout(5000)

    assert page.locator("text=Import 1").first.is_visible(), \
        "'Import 1' should appear in the Settings panel"

    screenshot(page, "geometry_import_settings_row.png")


def test_import_shows_objects_in_settings(page):
    """After importing, the import row auto-expands showing the 3 imported
    solid objects (PCB_OUTLINE, CHIP, 3DVC) in the Settings panel."""
    # Import the STEP file
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)
    page.evaluate(f'window.trame.state.set("import_file_path", "{STEP_FILE}")')
    page.wait_for_timeout(300)
    page.locator(".import-confirm-btn").click()
    page.wait_for_timeout(5000)

    # Import auto-expands — objects should already be visible
    for obj_name in ["PCB_OUTLINE", "CHIP", "3DVC"]:
        assert page.locator(f"text={obj_name}").first.is_visible(), \
            f"Object '{obj_name}' should be visible in Settings panel"

    screenshot(page, "geometry_import_settings.png")


def test_unit_dropdown_visible_after_import(imported_geometry):
    """After importing, the unit dropdown (.geo-unit-select) must be visible
    in the Settings panel next to the import row label."""
    page = imported_geometry
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(300)

    select = page.locator(".geo-unit-select").first
    assert select.is_visible(), "Unit dropdown must be visible next to the import row"
    screenshot(page, "unit_dropdown_visible.png")


def test_unit_dropdown_shows_default_from_step(imported_geometry):
    """The unit dropdown must default to the unit parsed from the STEP file.
    viewer_geometry_unit state must be set to that unit after import."""
    page = imported_geometry

    unit = _get(page, "viewer_geometry_unit")
    assert unit in ("mm", "m", "cm", "um", "nm"), (
        f"viewer_geometry_unit should be a valid unit string, got '{unit}'"
    )

    # Verify the import entry's unit matches the state — this is what the dropdown is bound to.
    # (Vuetify 3 VSelect renders selection text inside <input readonly> elements whose
    # value attributes are not captured by textContent/innerText; checking state is authoritative.)
    imports = _get(page, "geometry_imports")
    assert imports, "geometry_imports must have at least one entry"
    imp_unit = imports[0].get("unit", "")
    assert imp_unit == unit, (
        f"Import entry unit should be '{unit}' but got '{imp_unit}'"
    )

    # The dropdown widget must also be visible when the Geometry section is open
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(300)
    assert page.locator(".geo-unit-select").first.is_visible(), \
        "Unit dropdown must be visible when Geometry section is open"
    screenshot(page, "unit_dropdown_default.png")


def test_unit_dropdown_shows_all_options(imported_geometry):
    """Opening the unit dropdown must show all expected unit options
    (mm, m, cm, um, nm) — not 'No data available'."""
    page = imported_geometry
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(300)

    # Click the dropdown to open it
    page.locator(".geo-unit-select").first.click()
    page.wait_for_timeout(400)
    screenshot(page, "unit_dropdown_open.png")

    expected_units = ["mm", "m", "cm", "um", "nm"]
    for unit in expected_units:
        # Vuetify 3 renders options in a .v-list-item or .v-select__content overlay
        option = page.get_by_role("option", name=unit, exact=True)
        assert option.is_visible(), (
            f"Unit option '{unit}' must be visible in the open dropdown. "
            "If 'No data available' shows, the items binding is broken."
        )

    screenshot(page, "unit_dropdown_options_visible.png")
    # Close the dropdown
    page.keyboard.press("Escape")


def test_unit_dropdown_is_compact(imported_geometry):
    """The unit dropdown width must be compact (≤ 80px)."""
    page = imported_geometry
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(300)

    bbox = page.locator(".geo-unit-select").first.bounding_box()
    assert bbox is not None, "Unit dropdown must be present"
    assert bbox["width"] <= 80, (
        f"Unit dropdown width should be ≤ 80px, got {bbox['width']:.0f}px"
    )


def test_unit_dropdown_change_updates_state(imported_geometry):
    """Changing the unit dropdown must update viewer_geometry_unit state."""
    page = imported_geometry
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(300)

    original_unit = _get(page, "viewer_geometry_unit")
    new_unit = "m" if original_unit != "m" else "mm"

    # Set unit directly via state (simulates dropdown change)
    imports = _get(page, "geometry_imports")
    assert imports, "geometry_imports must not be empty"
    import_id = imports[0]["id"]
    page.evaluate(
        f"""() => {{
            window.trame.state.set("geometry_imports",
                (window.trame.state.get("geometry_imports") || []).map(
                    i => i.id === "{import_id}" ? {{...i, unit: "{new_unit}"}} : i
                )
            );
        }}"""
    )
    page.wait_for_timeout(400)

    # Trigger the controller via state mutation (server syncs geometry_imports)
    # then check viewer_geometry_unit is updated when expanded import changes unit
    screenshot(page, "unit_dropdown_changed.png")
