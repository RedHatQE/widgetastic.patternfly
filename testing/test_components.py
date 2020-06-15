from widgetastic_patternfly import Button, ViewChangeButton, Input, NavDropdown, BootstrapNav

def reprtest(view):
    for it in view.child_items:
        assert isinstance(str(it), str)
        assert isinstance(repr(it), str)


def test_srt_repr(browser):
    class TestView(View):
        btn = Button()
        vcb = ViewChangeButton()
        inp = Input()
        nav_dropdown = NavDropdown()
        bstnav = BootstrapNav

    view = TestView(browser)
    for item in view.btn, view.vcb, view.inp, view.nav_dropdown, view.bstnav:
        reprtest(item)
