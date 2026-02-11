"""
Geometry import workflow tests.

Verifies the STEP file import pipeline: opening the import dialog,
importing a file, and viewing imported objects in the Settings panel.
"""

from helpers import screenshot, STEP_FILE


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


def test_import_creates_tree_node(page):
    """After importing a STEP file, 'Import 1' should appear as a child
    node under Geometry in the Model Builder tree."""
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)

    page.evaluate(f'window.trame.state.set("import_file_path", "{STEP_FILE}")')
    page.wait_for_timeout(300)
    page.locator(".import-confirm-btn").click()
    page.wait_for_timeout(5000)

    assert page.locator("text=Import 1").first.is_visible(), \
        "'Import 1' should appear in the Model Builder tree"

    screenshot(page, "geometry_import_tree.png")


def test_import_shows_objects_in_settings(page):
    """Clicking 'Import 1' in the tree should show the 3 imported solid
    objects (PCB_OUTLINE, CHIP, 3DVC) in the Settings panel."""
    # Import the STEP file
    page.locator("text=Geometry").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Import STEP file...", exact=True).click()
    page.wait_for_timeout(500)
    page.evaluate(f'window.trame.state.set("import_file_path", "{STEP_FILE}")')
    page.wait_for_timeout(300)
    page.locator(".import-confirm-btn").click()
    page.wait_for_timeout(5000)

    # Click the import node to see object list
    page.locator("text=Import 1").first.click()
    page.wait_for_timeout(1000)

    for obj_name in ["PCB_OUTLINE", "CHIP", "3DVC"]:
        assert page.locator(f"text={obj_name}").first.is_visible(), \
            f"Object '{obj_name}' should be visible in Settings panel"

    screenshot(page, "geometry_import_settings.png")
