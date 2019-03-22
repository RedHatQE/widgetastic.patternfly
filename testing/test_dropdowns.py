from widgetastic.widget import Text, View
from widgetastic_patternfly import Kebab


def test_kebab(browser):
    class TestView(View):
        kebab_menu = Kebab(id="dropdownKebab")
        kebab_output = Text(locator='//*[@id="kebab_display"]')

    view = TestView(browser)

    # check for display
    assert view.kebab_menu.is_displayed

    # check dropdown open/close methods
    assert not view.kebab_menu.is_opened
    view.kebab_menu.open()
    assert view.kebab_menu.is_opened
    view.kebab_menu.close()
    assert not view.kebab_menu.is_opened

    # check for items
    assert view.kebab_menu.items == ["Action one", "Another action", "Separated link"]
    assert view.kebab_menu.has_item("Another action")
    assert not view.kebab_menu.has_item("kebab")

    # check selection
    for item in view.kebab_menu.items:
        view.kebab_menu.item_select(item)
        # closes by default after selection
        assert not view.kebab_menu.is_opened
        assert item == view.kebab_output.read()
