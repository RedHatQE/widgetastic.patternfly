# -*- coding: utf-8 -*-
from widgetastic.widget import View
from widgetastic_patternfly import Button


def test_button_click(browser):
    class TestView(View):
        any_button = Button()  # will pick up first button, basically. 'Default Normal' right now
        button1 = Button('Default Normal')
        button2 = Button(title='Destructive title')
        button3 = Button(title='noText', classes=[Button.PRIMARY])

    view = TestView(browser)
    assert view.any_button.is_displayed
    assert view.any_button.text == 'Default Normal'
    assert view.any_button.read() == 'Default Normal'
    assert view.button1.is_displayed
    assert view.button1.read() == 'Default Normal'
    assert view.button2.is_displayed
    assert view.button2.read() == 'Destructive'
    assert view.button2.title == 'Destructive title'
    assert view.button3.is_displayed
    assert view.button3.read() == ''
    assert view.button3.title == 'noText'

    FILL_DICT = {"any_button": True, "button1": True, "button2": False, "button3": False}
    assert view.fill(FILL_DICT)
