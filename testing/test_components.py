from widgetastic.widget import View
from widgetastic_patternfly import Button, ViewChangeButton, Input, NavDropdown, BootstrapNav

def reprtest(view):
    for wgt in view.sub_widgets:
        assert isinstance(str(wgt), str)
        assert isinstance(repr(wgt), str)


def test_srt_repr(browser):
    class TestView(View):
        btn = Button()
        vcb = ViewChangeButton(title="nonexistent")
        inp = Input()
        nav_dropdown = NavDropdown()
        bstnav = BootstrapNav

    view = TestView(browser)
    reprtest(view)
