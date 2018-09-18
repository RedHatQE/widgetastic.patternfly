import pytest

from widgetastic.exceptions import LocatorNotImplemented
from widgetastic.widget import View
from widgetastic_patternfly import AggregateStatusCard
from widgetastic_patternfly.utils import PFIcon


def test_agg_status_card_read(browser):
    """Test Aggregate Status Card reading number, title, notifications"""

    class TestAggView(View):
        agg_card_ip = AggregateStatusCard(name='Ipsum', action_title='Add Ipsum')
        agg_card_amet = AggregateStatusCard(name='Amet')
        agg_card_adi = AggregateStatusCard(name='Adipiscing')

    view = TestAggView(browser)

    # Display
    for card in [view.agg_card_ip, view.agg_card_amet, view.agg_card_adi]:
        assert card.is_displayed

    # count
    assert view.agg_card_ip.count == 0
    assert view.agg_card_amet.count == 20
    assert view.agg_card_adi.count is None

    # Clickable body with title, or not
    assert view.agg_card_ip.click_body_action() is None
    for card in [view.agg_card_amet, view.agg_card_adi]:
        with pytest.raises(LocatorNotImplemented):
            card.click_body_action()

    # title icons
    for card in [view.agg_card_ip, view.agg_card_adi]:
        assert card.icon == PFIcon.icons.HOME
    assert view.agg_card_amet.icon is None

    # notifications
    ip_notes_expected = [
        {'icon': PFIcon.icons.ADD, 'text': None}
    ]
    ip_notes = view.agg_card_ip.notifications
    assert len(ip_notes) == 1
    assert [n.read() for n in ip_notes] == ip_notes_expected

    amet_notes_expected = [
        {'icon': PFIcon.icons.ERROR, 'text': '4'},
        {'icon': PFIcon.icons.WARNING, 'text': '1'}
    ]
    amet_notes = view.agg_card_amet.notifications
    assert len(amet_notes) == 2
    assert [n.read() for n in amet_notes] == amet_notes_expected

    adi_notes_expected = [
        {'icon': None, 'text': 'noclick'}
    ]
    adi_notes = view.agg_card_adi.notifications
    assert len(adi_notes) == 1
    assert [n.read() for n in adi_notes] == adi_notes_expected

    assert view.agg_card_ip.read() == {
        'icon': PFIcon.icons.HOME,
        'count': 0,
        'name': 'Ipsum',
        'notifications': ip_notes_expected
    }
