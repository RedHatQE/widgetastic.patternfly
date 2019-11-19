import re
from collections import namedtuple

from widgetastic.widget import View
from widgetastic_patternfly import FlashMessages

Message = namedtuple('Message', 'text type')

MSGS = [Message('Retirement date set to 12/31/19 15:55 UTC', 'success'),
        Message('Retirement date removed', 'success'),
        Message('All changes have been reset', 'warning'),
        Message('Set/remove retirement date was cancelled by the user', 'success'),
        Message('Retirement initiated for 1 VM and Instance from the CFME Database', 'success')]


def test_flashmessage(browser):
    class TestView(View):
        flash = FlashMessages('.//div[@id="flash_msg_div"]')

    view = TestView(browser)
    msgs = view.flash.read()
    assert len(msgs) == len(MSGS)
    for i in range(len(msgs)):
        assert msgs[i] == MSGS[i].text

    view.flash.assert_no_error()

    # regex match
    t = re.compile('^Retirement')
    view.flash.assert_message(t)
    view.flash.assert_success_message(t)

    # partial match
    t = 'etirement'
    view.flash.assert_message(t, partial=True)
    view.flash.assert_success_message(t, partial=True)

    # inverse match
    t = 'This message does not exist'
    assert not view.flash.match_messages(t)
    assert view.flash.match_messages(t, inverse=True)

    view.flash.dismiss()
    assert not view.flash.read()
