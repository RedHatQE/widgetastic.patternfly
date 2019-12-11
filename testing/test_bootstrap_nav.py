from widgetastic.utils import partial_match
from widgetastic.widget import View
from widgetastic_patternfly import BootstrapNav


def test_bootstrap_nav(browser):
    class TestView(View):
        nav = BootstrapNav('.//div/ul[@class="nav nav-pills nav-stacked"]')

    view = TestView(browser)

    # assert that nav is visible
    assert view.nav.is_displayed
    # Check if all options are being returned
    assert view.nav.all_options == [
        "ALL (Default)",
        "Environment / Dev",
        "Environment / Prod",
        "UAT",
        "Environment / UAT",
        "",
    ]
    # assert if currently active(selected) element is being returned correctly
    assert view.nav.read() == ['ALL (Default)']
    # assert if list has_item
    assert view.nav.has_item(text='Environment / Prod')
    # assert if partial match works for is_disabled
    assert view.nav.is_disabled(text=partial_match("UAT"))
