# -*- coding: utf-8 -*-
from wait_for import wait_for

from widgetastic.widget import TextInput
from widgetastic.widget import View
from widgetastic_patternfly import Modal, Button

# Values from testing_page.html modal
modal_id = 'myModal'
title = 'Modal Title'


class SpecificModal(Modal):
    """ Specific Modal class overwrites the body of Modal, since the form will vary. """

    @View.nested
    class body(View):  # noqa
        field_one = TextInput(id="textInput-modal-markup")
        field_two = TextInput(id="textInput2-modal-markup")
        field_three = TextInput(id="textInput3-modal-markup")


def test_generic_modal(browser):
    """
    Test the modal, including all methods/properties

    Test against modal defined in testing_page.html
    :param browser: browser fixture
    """

    class TestView(View):
        """ Dummy page matching testing_page.html elements"""
        button = Button('Launch demo modal')
        modal = SpecificModal(id=modal_id)

    view = TestView(browser)
    assert not view.modal.is_displayed

    # Open the modal
    assert not view.button.disabled
    view.button.click()
    wait_for(lambda: view.modal.is_displayed, delay=0.5, num_sec=5)

    assert view.modal.title == title

    # close the modal via the "x"
    view.modal.close()
    view.flush_widget_cache()
    wait_for(lambda: not view.modal.is_displayed, delay=0.5, num_sec=5)

    # open modal again
    view.button.click()
    wait_for(lambda: view.modal.is_displayed, delay=0.5, num_sec=5)
    # make sure buttons are not disabled
    assert not view.modal.footer.dismiss.disabled
    assert not view.modal.footer.accept.disabled
    # make sure the cancel button works
    view.modal.dismiss()
    wait_for(lambda: not view.modal.is_displayed, delay=0.1, num_sec=5)

    # open modal to fill the form
    view.button.click()
    wait_for(lambda: view.modal.is_displayed, delay=0.5, num_sec=5)
    assert view.fill(
        {"modal": {"body": {"field_one": "value1", "field_two": "value2", "field_three": "value3"}}}
    )
    # make sure accept button works
    view.modal.accept()
    wait_for(lambda: not view.modal.is_displayed, delay=0.1, num_sec=5)
