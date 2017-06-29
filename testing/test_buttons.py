# -*- coding: utf-8 -*-
from widgetastic.widget import View
from widgetastic_patternfly import Button


def test_button_click(browser):
    class TestView(View):
        any_button = Button()
        button1 = Button('Default Normal')
        button2 = Button(title='Destructive title')
        button3 = Button(title='noText', classes=[Button.PRIMARY])

    view = TestView(browser)
    assert view.any_button.is_displayed
    assert view.button1.is_displayed
    assert view.button2.is_displayed
    assert view.button3.is_displayed
