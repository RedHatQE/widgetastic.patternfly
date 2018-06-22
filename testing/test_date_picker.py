import random
from datetime import datetime, timedelta

from widgetastic.widget import View
from widgetastic_patternfly import DatePicker


def test_bootstrap_date_picker(browser):
    class TestView(View):
        dp_readwrite = DatePicker(name="date_readwrite")
        dp_readonly = DatePicker(id="date_readonly")
        dp_basic_patternfly = DatePicker(id="patternfly_dp")

    view = TestView(browser)

    # `readonly` property working or not
    assert view.dp_readonly.readonly
    assert not view.dp_readwrite.readonly

    # `fill` and `read` with current date
    today_date = datetime.now()
    view.dp_readonly.fill(today_date)
    assert today_date.date() == view.dp_readonly.read().date()
    view.dp_readwrite.fill(today_date)
    assert today_date.date() == view.dp_readwrite.read().date()
    view.dp_basic_patternfly.fill(today_date)
    assert today_date.date() == view.dp_basic_patternfly.read().date()

    # check `fill` and `read` with year back date
    yr_back_date = (today_date - timedelta(days=365))
    view.dp_readonly.fill(yr_back_date)
    assert yr_back_date.date() == view.dp_readonly.read().date()
    view.dp_readwrite.fill(yr_back_date)
    assert yr_back_date.date() == view.dp_readwrite.read().date()
    view.dp_basic_patternfly.fill(yr_back_date)
    assert yr_back_date.date() == view.dp_basic_patternfly.read().date()

    # check if date already selected `fill` should return False
    view.dp_readonly.fill(datetime.now())
    assert not view.dp_readonly.fill(datetime.now())
    view.dp_readwrite.fill(datetime.now())
    assert not view.dp_readwrite.fill(datetime.now())
    view.dp_basic_patternfly.fill(datetime.now())
    assert not view.dp_basic_patternfly.fill(datetime.now())

    # `fill` and `read` with random timedelta
    random_weeks = random.randint(100, 5000)
    date_obj = (today_date - timedelta(weeks=random_weeks))

    view.dp_readonly.fill(date_obj)
    assert date_obj.date() == view.dp_readonly.read().date()
    view.dp_readwrite.fill(date_obj)
    assert date_obj.date() == view.dp_readwrite.read().date()
    view.dp_basic_patternfly.fill(date_obj)
    assert date_obj.date() == view.dp_basic_patternfly.read().date()
