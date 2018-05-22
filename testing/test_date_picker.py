from widgetastic.widget import View
from widgetastic_patternfly import DatePicker
from datetime import datetime, timedelta


def test_bootstrap_date_picker(browser):
    class TestView(View):
        dp_readwrite = DatePicker(name="date_readwrite")
        dp_readonly = DatePicker(id="date_readonly")

    view = TestView(browser)

    # `is_readonly` proprety working or not
    assert view.dp_readonly.is_readonly
    assert not view.dp_readwrite.is_readonly

    # `fill` and `read` with current date
    today_date = datetime.now()
    view.dp_readonly.fill(today_date)
    assert today_date.date() == view.dp_readonly.read().date()

    view.dp_readwrite.fill(today_date)
    assert today_date.date() == view.dp_readwrite.read().date()

    # `fill` and `read` with year back date
    yr_back_date = (today_date - timedelta(days=365))
    view.dp_readonly.fill(yr_back_date)
    assert yr_back_date.date() == view.dp_readonly.read().date()

    view.dp_readwrite.fill(yr_back_date)
    assert yr_back_date.date() == view.dp_readwrite.read().date()
