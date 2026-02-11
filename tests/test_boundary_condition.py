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

from helpers import screenshot


def _get(page, key):
    return page.evaluate(f'window.trame.state.get("{key}")')


def _expand_bc_and_click_power_source(page):
    """Helper: expand Boundary Condition and click Power Source."""
    page.locator("text=Boundary Condition").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Power Source", exact=True).first.click()
    page.wait_for_timeout(500)


def test_power_map_removed(page):
    """'Power Map' should no longer appear in the Model Builder tree
    (it was absorbed into Boundary Condition)."""
    assert not page.locator("text=Power Map").first.is_visible()


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
    page.locator("text=Boundary Condition").first.click()
    page.wait_for_timeout(500)
    page.get_by_text("Temperature", exact=True).first.click()
    page.wait_for_timeout(500)

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
