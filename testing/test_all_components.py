"""
This module contains code for auto-discovering Widget classes, instantiating
them in a programatically defined view class as a new type, which is then
instantiated. The widgets appear to get instantiated upon accessing them in the instantiated view.
After all of this, the behavior of the widget objects can be tested.
"""

from widgetastic.utils import attributize_string
from widgetastic.widget import View, Widget
import widgetastic_patternfly as wp
import inspect
import pytest


collected_widgets = {
    name: t for name, t in inspect.getmembers(wp)
    if (inspect.isclass(t) and issubclass(t, Widget)
        and not issubclass(t, wp.ParametrizedView))}
""" Subclasses of Widget from the widgetastic_patternfly module (including
it's own imports), that are gonna be tested. Not including the
ParametrizedView. """


DUMMY_NAME = "name_of_the_dummy"
DUMMY_ID = "id_of_the_dummy"
DUMMY_LOCATOR = "/dummy"
DUMMY_TREE_ID = "SOME_DUMMY_TREE_ID"


# TODO generate from args spec that should by added to definition of the types.
# Currently some parameters that are enough to successfully construct the
# instance from the type are chosen.
init_values = {
    wp.AggregateStatusCard: dict(name=DUMMY_NAME),
    wp.AggregateStatusMiniCard: dict(name=DUMMY_NAME, locator=DUMMY_LOCATOR),
    wp.BarChart: dict(id=DUMMY_ID),
    wp.BootstrapNav: dict(locator=DUMMY_LOCATOR),
    wp.BootstrapSelect: dict(locator=DUMMY_LOCATOR),
    wp.BootstrapSwitch: dict(id=DUMMY_ID),
    wp.DatePicker: dict(id=DUMMY_ID),
    wp.Dropdown: dict(text=DUMMY_NAME),
    wp.GroupedBarChart: dict(id=DUMMY_ID),
    wp.Kebab: dict(id=DUMMY_ID),
    wp.LineChart: dict(id=DUMMY_ID),
    wp.SelectorDropdown: dict(button_attr=DUMMY_LOCATOR, button_attr_value=DUMMY_NAME),
    wp.SingleLineChart: dict(id=DUMMY_ID),
    wp.SingleSplineChart: dict(id=DUMMY_ID),
    wp.SplineChart: dict(id=DUMMY_ID),
    wp.SparkLineChart: dict(id=DUMMY_ID),
    wp.StatusNotification: dict(note_element=DUMMY_LOCATOR),
    wp.Table: dict(locator=DUMMY_LOCATOR),
    wp.Text: dict(locator=DUMMY_LOCATOR),
    wp.ViewChangeButton: dict(title=DUMMY_NAME),
    wp.VerticalNavigation: dict(locator=DUMMY_LOCATOR),
}
""" Dicts with the values for __init__ methods of the `collected_widgets`.  """


@pytest.fixture(scope="module")
def test_view_class():
    """ Returns an subclass of View with the collected_widgets instantiated
    and assigned to it. """

    # Instantiate objects to be set in the view with required params for __init__.
    attributes = {f'{attributize_string(name)}': cls(**init_values.get(cls, {}))
                  for name, cls in collected_widgets.items()}

    # Required for the Tree widgets to function properly.
    attributes['tree_id'] = DUMMY_TREE_ID

    view_class = type('TheTestView', (View,), attributes)
    return view_class


@pytest.fixture
def test_view(browser, test_view_class):
    view = test_view_class(browser)
    return view


@pytest.mark.parametrize('widget_name', collected_widgets.keys())
def test_widget_init(test_view, widget_name):
    """ Test basic instantiation of the widgets in a view.

    When a View like this is defined:
    ```
        class MyView(View):
            btn = Button(id="some_id")

        view = MyView(browser)
    ```

    The Button.__init__ seem to be delayed until the view.btn is accessed.
    We got the view as the test_view fixture, so we now need to access it to
    check it won't produce an exception. """

    assert getattr(test_view, attributize_string(widget_name))


@pytest.mark.parametrize('widget_name', collected_widgets.keys())
def test_widget_stringification(test_view, widget_name):
    """ Tests whether the widget can be stringified.
    All the widgets that can be instantiated should be able to stringify."""
    wgt = getattr(test_view, attributize_string(widget_name))
    assert isinstance(str(wgt), str)
    assert isinstance(repr(wgt), str)
