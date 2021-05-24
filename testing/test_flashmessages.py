import re
from collections import namedtuple

from widgetastic.widget import View
from widgetastic_patternfly import FlashMessages

Message = namedtuple('Message', 'text type')

OK_MSGS = [
    Message('Retirement date set to 12/31/19 15:55 UTC', 'success'),
    Message('Retirement date removed', 'success'),
    Message('All changes have been reset', 'warning'),
    Message('Set/remove retirement date was cancelled by the user', 'success'),
    Message('Retirement initiated for 1 VM and Instance from the CFME Database', 'success'),
]
ERROR_MSGS = [Message('Not Configured', 'error')]
MSGS = OK_MSGS + ERROR_MSGS


def test_flashmessage(browser):
    class TestView(View):
        flash = View.nested(FlashMessages)

    view = TestView(browser)
    msgs = view.flash.read()
    assert len(msgs) == len(MSGS)
    for msg, MSG in zip(msgs, MSGS):
        assert msg == MSG.text

    # Verify assert_no_error() with ignore_messages, then dismiss the error messages
    view.flash.assert_no_error(ignore_messages=[msg.text for msg in ERROR_MSGS])
    for msg in view.flash.messages():
        if msg.type == 'error':
            msg.dismiss()

    # Verify assert_no_error()
    view.flash.assert_no_error()

    # Test regex match.
    t = re.compile('^Retirement')
    view.flash.assert_message(t)
    view.flash.assert_success_message(t)

    # Test partial pattern match.
    t = 'etirement'
    view.flash.assert_message(t, partial=True)
    view.flash.assert_success_message(t, partial=True)

    # Test inverse pattern match.
    t = 'This message does not exist'
    assert view.flash.read(text=t, inverse=True) == [msg.text for msg in OK_MSGS]

    view.flash.dismiss()
    assert not view.flash.read()
