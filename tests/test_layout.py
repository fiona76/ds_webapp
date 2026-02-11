"""
Layout and panel visibility tests.

Verifies that the app shell renders correctly on launch and that
panel collapse toggles work as expected.
"""

from helpers import screenshot


# -- Tree nodes expected in Model Builder (Power Map was removed) ----------

EXPECTED_TREE_NODES = [
    "Geometry",
    "Boundary Condition",
    "Materials",
    "Modelization",
    "Build Sub-Model",
    "Solving",
    "Result",
]


def test_all_panels_visible(page):
    """On app launch, all panels should be visible: Model Builder, Settings, Log,
    title bar, and all 7 tree nodes in the Model Builder."""
    assert page.locator("text=DS WebApp").first.is_visible()
    assert page.locator("text=Model Builder").first.is_visible()
    assert page.locator("text=Settings").first.is_visible()
    assert page.locator("text=Log").first.is_visible()

    for node_name in EXPECTED_TREE_NODES:
        assert page.locator(f"text={node_name}").first.is_visible(), \
            f"Tree node '{node_name}' should be visible on launch"

    screenshot(page, "layout_all_open.png")


def test_left_panels_collapse(page):
    """Clicking the left-arrow toggle should hide both Model Builder and
    Settings panels, while the Log panel stays visible."""
    page.locator(".toggle-model-builder").click()
    page.wait_for_timeout(500)

    assert not page.locator("text=Model Builder").first.is_visible()
    assert not page.locator("text=Settings").first.is_visible()
    assert page.locator("text=Log").first.is_visible(), \
        "Log panel should remain visible when only left panels are collapsed"

    screenshot(page, "layout_left_collapsed.png")


def test_all_panels_collapse(page):
    """Collapsing left panels AND the log panel should leave only the
    menu bar and viewport visible."""
    # Collapse left panels
    page.locator(".toggle-model-builder").click()
    page.wait_for_timeout(300)
    # Collapse log panel
    page.locator(".toggle-log").click()
    page.wait_for_timeout(500)

    assert not page.locator("text=Model Builder").first.is_visible()
    assert not page.locator("text=Settings").first.is_visible()
    assert not page.locator("text=Log").first.is_visible()

    screenshot(page, "layout_panels_closed.png")
