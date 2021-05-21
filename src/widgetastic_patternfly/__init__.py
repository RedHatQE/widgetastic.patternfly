# -*- coding: utf-8 -*-
"""This package contains classes that represent widgets in Patternfly for Widgetastic"""
import functools
import re
import time
from cached_property import cached_property
from collections import namedtuple
from datetime import datetime
from operator import not_

from widgetastic.exceptions import (
    LocatorNotImplemented,
    NoSuchElementException,
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
    WidgetOperationFailed,
)
from widgetastic.log import call_sig
from widgetastic.widget import (
    BaseInput,
    ClickableMixin,
    Table,
    Text,
    TextInput,
    View,
    Widget,
    do_not_read_this_widget,
    ParametrizedView
)
from widgetastic.utils import ParametrizedLocator, Parameter, VersionPick, partial_match
from widgetastic.xpath import quote

from wait_for import wait_for, wait_for_decorator, TimedOutError

from .utils import PFIcon

# py3.7+ module change
try:
    Pattern = re.Pattern
except AttributeError:
    Pattern = re._pattern_type


def retry_element(method):
    """Decorator to invoke method one or more times, if StaleElementReferenceException or
    NoSuchElementException are raised.
    """
    @functools.wraps(method)
    def retry_element_wrapper(*args, **kwargs):
        attempts = 10
        for i in range(attempts):
            try:
                return method(*args, **kwargs)
            except (StaleElementReferenceException, NoSuchElementException):
                if i < attempts - 1:
                    time.sleep(0.5)
                else:
                    raise

    return retry_element_wrapper


class CandidateNotFound(Exception):
    """
    Raised if there is no candidate found whilst trying to traverse a tree.
    """
    def __init__(self, d):
        self.d = d

    @property
    def message(self):
        return ", ".join("{}: {}".format(k, v) for k, v in self.d.items())

    def __str__(self):
        return self.message


class DropdownDisabled(Exception):
    pass


class DropdownItemDisabled(Exception):
    pass


class DropdownItemNotFound(Exception):
    pass


class SelectItemNotFound(Exception):
    def __init__(self, widget, item, options=None):
        self.widget = widget
        self.item = item
        self.options = options

    @property
    def message(self):
        return ('Could not find {!r} in {!r}\n'
                'These options are present: {!r}'
                .format(self.item, self.widget, ', '.join(self.options)))

    def __str__(self):
        return self.message


class Button(Widget, ClickableMixin):
    """A PatternFly/Bootstrap button

    You can match by text, partial text or by attributes, you can also add the bootstrap classes
    into the matching.

    .. code-block:: python

        Button('Text of button (unless it is an input ...)')
        Button('contains', 'Text of button (unless it is an input ...)')
        Button(title='Show xyz')  # And such
        Button('Add', classes=[Button.PRIMARY])
        assert button.active
        assert not button.disabled
    """
    CHECK_VISIBILITY = True

    # Classes usable in the constructor
    # Button types
    DEFAULT = 'btn-default'
    PRIMARY = 'btn-primary'
    SUCCESS = 'btn-success'
    INFO = 'btn-info'
    WARNING = 'btn-warning'
    DANGER = 'btn-danger'
    LINK = 'btn-link'

    # Button sizes
    LARGE = 'btn-lg'
    MEDIUM = 'btn-md'
    SMALL = 'btn-sm'
    EXTRA_SMALL = 'btn-xs'

    # Shape
    BLOCK = 'btn-block'

    def __init__(self, parent, *text, **kwargs):
        logger = kwargs.pop('logger', None)
        Widget.__init__(self, parent, logger=logger)
        self.args = text
        self.kwargs = kwargs
        classes = kwargs.pop('classes', [])
        if text:
            if kwargs:  # classes should have been the only kwarg combined with text args
                raise TypeError('If you pass button text then only pass classes in addition')
            if len(text) == 1:
                self.locator_conditions = 'normalize-space(.)={}'.format(quote(text[0]))
            elif len(text) == 2 and text[0].lower() == 'contains':
                self.locator_conditions = 'contains(normalize-space(.), {})'.format(quote(text[1]))
            else:
                raise TypeError('An illegal combination of text params')
        else:
            # Join the kwargs, if any
            self.locator_conditions = ' and '.join(
                ['@{}={}'.format(attr, quote(value))
                 for attr, value in kwargs.items()]
            )

        if classes:
            if self.locator_conditions:
                self.locator_conditions += ' and '
            self.locator_conditions += ' and '.join(
                'contains(@class, {})'.format(quote(klass))
                for klass in classes)
        if self.locator_conditions:
            self.locator_conditions = 'and ({})'.format(self.locator_conditions)

    # TODO: Handle input value the same way as text for other tags
    def __locator__(self):
        return (
            './/*[(self::a or self::button or (self::input and (@type="button" or @type="submit")))'
            ' and contains(@class, "btn") {}]'.format(self.locator_conditions))

    @property
    def active(self):
        return 'active' in self.browser.classes(self)

    @property
    def disabled(self):
        return ('disabled' in self.browser.classes(self) or
                self.browser.get_attribute('disabled', self) == 'disabled' or
                self.browser.get_attribute('disabled', self) == 'true')

    def __repr__(self):
        return '{}{}'.format(type(self).__name__, call_sig(self.args, self.kwargs))

    @property
    def title(self):
        return self.browser.get_attribute('title', self)

    def fill(self, value):
        if value:
            self.click()
            return True
        else:
            return False

    @property
    def text(self):
        """Return the element text, not the passed text"""
        return self.browser.text(self)

    def read(self):
        """Widget.read override, use text"""
        return self.text


class ViewChangeButton(Widget, ClickableMixin):
    """A PatternFly/Bootstrap view selection button in CFME 56z

        .. code-block:: python

            ViewChangeButton(title='Grid View')
            assert button.active
    """
    CHECK_VISIBILITY = True

    def __init__(self, parent, title, **kwargs):
        Widget.__init__(self, parent, logger=kwargs.pop('logger', None))
        self.title = title

    def __locator__(self):
        return './/a[(@title={}) and i[contains(@class, "fa")]]'.format(quote(self.title))

    @property
    def active(self):
        return 'active' in self.browser.classes('..', parent=self)


class Input(TextInput):
    """Patternfly input

    Has some additional methods.
    """
    WARNING_LOCATOR = "./following-sibling::div"
    HELP_BLOCK_LOCATOR = "./following-sibling::span"

    @property
    def help_block(self):
        e = self.browser.element(self)
        try:
            help_block = self.browser.element(self.HELP_BLOCK_LOCATOR, parent=e)
        except NoSuchElementException:
            return None
        else:
            return self.browser.text(help_block)

    @property
    def warning(self):
        try:
            self.browser.wait_for_element(self.WARNING_LOCATOR, timeout=3)
            return self.browser.text(self.WARNING_LOCATOR)
        except NoSuchElementException:
            return None


class NavDropdown(Widget, ClickableMixin):
    """The dropdowns used eg. in navigation. Usually located in the top navbar."""
    EXPAND_LOCATOR = ('./a["aria-expanded" and '
                      '"aria-haspopup" and '
                      'contains(@class, "dropdown-toggle")]')
    TEXT_LOCATOR = './a//p'

    ROOT = ParametrizedLocator('//nav'
                               '//li[.//a[@id={@id|quote} and contains(@class, "dropdown-toggle")]'
                               ' and contains(@class, "dropdown")]')

    def __init__(self, parent, id=None, logger=None):
        """id is optional to allow for easy subclass change of ROOT"""
        Widget.__init__(self, parent, logger=logger)
        self.id = id

    def read(self):
        return self.text

    @property
    def expandable(self):
        try:
            self.browser.element(self.EXPAND_LOCATOR)
        except NoSuchElementException:
            return False
        else:
            return True

    @property
    def expanded(self):
        if not self.expandable:
            return False
        return 'open' in self.browser.classes(self)

    @property
    def collapsed(self):
        return not self.expanded

    def expand(self):
        if not self.expandable:
            raise ValueError('{} is not expandable'.format(self.locator))
        if not self.expanded:
            self.click()
            if not self.expanded:
                raise Exception('Could not expand {}'.format(self.locator))
            else:
                self.logger.info('expanded')

    def collapse(self):
        if not self.expandable:
            return
        if self.expanded:
            self.click()
            if self.expanded:
                raise Exception('Could not collapse {}'.format(self.locator))
            else:
                self.logger.info('collapsed')

    @property
    def text(self):
        try:
            el = self.browser.element(self.TEXT_LOCATOR)
            return self.browser.text(el, parent=self)
        except NoSuchElementException:
            return None

    @property
    def icon(self):
        try:
            el = self.browser.element('./a/span[contains(@class, "pficon")]', parent=self)
            for class_ in self.browser.classes(el):
                if class_.startswith('pficon-'):
                    return class_[7:]
            else:
                return None
        except NoSuchElementException:
            return None

    @property
    def items(self):
        return [
            self.browser.text(element)
            for element
            in self.browser.elements('./ul/li[not(contains(@class, "divider"))]', parent=self)]

    def has_item(self, item):
        return item in self.items

    def item_enabled(self, item):
        if not self.has_item(item):
            raise ValueError('There is not such item {}'.format(item))
        element = self.browser.element(
            './ul/li[normalize-space(.)={}]'.format(quote(item)), parent=self)
        return 'disabled' not in self.browser.classes(element)

    def select_item(self, item):
        if not self.item_enabled(item):
            raise ValueError('Cannot click disabled item {}'.format(item))

        self.expand()
        self.logger.info('selecting item {}'.format(item))
        self.browser.click('./ul/li[normalize-space(.)={}]'.format(quote(item)), parent=self)

    def __repr__(self):
        return '{}(id={!r})'.format(type(self).__name__, self.id)


class BootstrapNav(Widget):
    """Encapsulate a Bootstrap nav component

    PatternFly is based on Bootstrap, and thus many of the Bootstrap components are available to
    PatternFly users. This widget provides convenience methods for the Bootstrap nav component for
    clicking on links and determining if an item in the nav is disabled.

    When instantiating this widget, use the XPath locator to point to exactly which Bootstrap nav
    you wish to work with.

    .. _code:: python

       nav = BootstrapNav('//div[id="main"]/ul[@contains(@class, "nav")]')

    See http://getbootstrap.com/components/#nav for more information on Bootstrap nav components.
    """
    ROOT = ParametrizedLocator('{@locator}')
    ITEM_LOCATOR = './/li'
    CURRENTLY_SELECTED = './/li[contains(@class, "active")]/a'
    TEXT_MATCHING = './/li/a[text()={txt}]'
    PARTIAL_TEXT = './/li/a[contains(normalize-space(.), {txt})]'
    ATTR_MATCHING = './/li/a[@{attr}={txt}]'
    TEXT_DISABLED = './/li[contains(@class, "disabled")]/a[text()={txt}]'
    PARTIAL_TEXT_DISABLED = (
        './/li[contains(@class, "disabled")]/a[contains(normalize-space(.), {txt})]'
    )
    ATTR_DISABLED = './/li[contains(@class, "disabled")]/a[@{attr}={txt}]'
    VALID_ATTRS = {'href', 'title', 'class', 'id'}

    def __init__(self, parent, locator, logger=None):
        """Create the widget"""
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __repr__(self):
        """String representation of this object"""
        return '{}({!r})'.format(type(self).__name__, self.locator)

    @property
    def currently_selected(self):
        """A property to return the currently selected menu item"""
        return [self.browser.text(el) for el in self.browser.elements(self.CURRENTLY_SELECTED)]

    @property
    def all_options(self):
        """A property to return the list of options available in the BootstrapNav"""
        b = self.browser
        return [b.text(el) for el in b.elements(self.ITEM_LOCATOR)]

    def read(self):
        """Implement read()"""
        return self.currently_selected

    def select(self, text=None, **kwargs):
        """
            Select/click an item from the menu

            Args:
                text: text of the link to be selected, If you want to partial text match,
                 use the :py:class:`BootstrapNav.partial` to wrap the value.
        """
        if text:
            # Select an item based on the text of that item
            if isinstance(text, partial_match):
                text = text.item
                link = self.browser.element(self.PARTIAL_TEXT.format(txt=quote(text)), parent=self)
                self.logger.info('selecting by partial matching text: %r', text)
            else:
                link = self.browser.element(self.TEXT_MATCHING.format(txt=quote(text)), parent=self)
                self.logger.info('selecting by full matching text: %r', text)
        elif self.VALID_ATTRS & set(kwargs.keys()):
            # Select an item based on an attribute, if it is one of the VALID_ATTRS
            attr = (self.VALID_ATTRS & set(kwargs.keys())).pop()
            link = self.browser.element(
                self.ATTR_MATCHING.format(attr=attr, txt=quote(kwargs[attr])))
        else:
            # If neither text, nor one of the VALID_ATTRS is supplied, raise a KeyError
            raise KeyError(
                'Either text or one of {} needs to be specified'.format(self.VALID_ATTRS))
        self.browser.click(link)

    def is_disabled(self, text=None, **kwargs):
        """Check if an item is disabled"""
        if text:
            # Check if an item is disabled based on the text of that item
            if isinstance(text, partial_match):
                partial_text = text.item
                xpath = self.PARTIAL_TEXT_DISABLED.format(txt=quote(partial_text))
            else:
                xpath = self.TEXT_DISABLED.format(txt=quote(text))
        elif self.VALID_ATTRS & set(kwargs.keys()):
            # Check if an item is disabled based on an attribute, if it is one of the VALID_ATTRS
            attr = (self.VALID_ATTRS & set(kwargs.keys())).pop()
            xpath = self.ATTR_DISABLED.format(attr=attr, txt=quote(kwargs[attr]))
        else:
            # If neither text, nor one of the VALID_ATTRS is supplied, raise a KeyError
            raise KeyError(
                'Either text or one of {} needs to be specified'.format(self.VALID_ATTRS))
        try:
            self.browser.element(xpath, parent=self)
            return True
        except NoSuchElementException:
            return False

    def has_item(self, text=None, **kwargs):
        """Check if an item with this name or attributes exists"""
        if text:
            # Check if an item exists based on the text of that item
            xpath = self.TEXT_MATCHING.format(txt=quote(text))
        elif self.VALID_ATTRS & set(kwargs.keys()):
            # Check if an item exists based on an attribute, if it is one of the VALID_ATTRS
            attr = (self.VALID_ATTRS & set(kwargs.keys())).pop()
            xpath = self.ATTR_MATCHING.format(attr=attr, txt=quote(kwargs[attr]))
        else:
            # If neither text, nor one of the VALID_ATTRS is supplied, raise a KeyError
            raise KeyError(
                'Either text or one of {} needs to be specified'.format(self.VALID_ATTRS))
        try:
            self.browser.element(xpath, parent=self)
            return True
        except NoSuchElementException:
            return False


class VerticalNavigation(Widget):
    """The Patternfly Vertical navigation."""
    CURRENTLY_SELECTED = './/li[contains(@class, "active")]/a'
    LINKS = './li/a'
    ITEMS_MATCHING = './li[a[normalize-space(.)={}]]'
    DIV_LINKS_MATCHING = './ul/li/a[span[normalize-space(.)={txt}] or @href={txt}]'
    SUB_LEVEL = './following-sibling::div[contains(@class, "nav-pf-")]'
    SUB_ITEM_LIST = './div[contains(@class, "nav-pf-")]/ul'
    CHILD_UL_FOR_DIV = './li[a[normalize-space(.)={}]]/div[contains(@class, "nav-pf-")]/ul'
    MATCHING_LI_FOR_DIV = './ul/li[a[span[normalize-space(.)={}]]]'

    def __init__(self, parent, locator, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __locator__(self):
        return self.locator

    def read(self):
        return self.currently_selected

    def nav_links(self, *levels):
        if not levels:
            return [self.browser.text(el) for el in self.browser.elements(self.LINKS, parent=self)]
        # Otherwise
        current_item = self
        for i, level in enumerate(levels):
            li = self.browser.element(
                self.ITEMS_MATCHING.format(quote(level)),
                parent=current_item)

            try:
                current_item = self.browser.element(self.SUB_ITEM_LIST, parent=li)
            except NoSuchElementException:
                if i == len(levels) - 1:
                    # It is the last one
                    return []
                else:
                    raise

        return [
            self.browser.text(el) for el in self.browser.elements(self.LINKS, parent=current_item)]

    def nav_item_tree(self, start=None):
        start = start or []
        result = {}
        for item in self.nav_links(*start):
            sub_items = self.nav_item_tree(start=start + [item])
            result[item] = sub_items or None
        if result and all(value is None for value in result.values()):
            # If there are no child nodes, then just make it a list
            result = list(result)  # list of keys
        return result

    @property
    def currently_selected(self):
        return [
            self.browser.text(el)
            for el
            in self.browser.elements(self.CURRENTLY_SELECTED, parent=self)]

    def select(self, *levels, handle_alert=True, anyway=True):
        """Select an item in the navigation.
        Args:
            *levels: Items to be clicked in the navigation.
        Keywords:
            handle_alert(bool): If set to True, will call self.browser.handle_alert to handle
            alert popups.
            anyway(bool): Default behaviour is that if you try selecting an already selected item,
            it will click it anyway. If you pass ``anyway=False``, it won't click it.
        """
        levels = list(levels)
        self.logger.info('Selecting %r in navigation', levels)
        if levels == self.currently_selected and not anyway:
            return

        passed_levels = []
        current_div = self.get_child_div_for(*passed_levels)
        for level in levels:
            passed_levels.append(level)
            finished = passed_levels == levels
            link = self.browser.element(
                self.DIV_LINKS_MATCHING.format(txt=quote(level)), parent=current_div)
            expands = bool(
                self.browser.elements(self.SUB_LEVEL, parent=link))
            if expands and not finished:
                self.logger.debug('moving to %s to open the next level', level)
                # No safety check because previous command did it
                self.browser.move_to_element(link, check_safe=False)

                @wait_for_decorator(timeout='10s', delay=0.2)
                def other_div_displayed():
                    return 'is-hover' in self.browser.classes(
                        self.MATCHING_LI_FOR_DIV.format(quote(level)),
                        parent=current_div)

                new_div = self.get_child_div_for(*passed_levels)
                # No safety check because previous command did it
                self.browser.move_to_element(new_div, check_safe=False)
                current_div = new_div
            elif not expands and not finished:
                raise ValueError(
                    'You are trying to expand {!r} which cannot be expanded'.format(passed_levels))
            else:
                # finished
                self.logger.debug('finishing the menu selection by clicking on %s', level)
                # No safety check because previous command did it
                self.browser.click(link, ignore_ajax=True, check_safe=False)
                if handle_alert:
                    self.browser.handle_alert(wait=2.0, squash=True)

    def get_child_div_for(self, *levels):
        current = self
        for level in levels:
            try:
                current = self.browser.element(
                    self.CHILD_UL_FOR_DIV.format(quote(level)),
                    parent=current)
            except NoSuchElementException:
                return None

        return self.browser.element('..', parent=current)

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.locator)


class Tab(View):
    """Represents the Tab widget.

    Selects itself automatically when any child widget gets accessed, ensuring that the widget is
    visible.

    You can specify your own ``ROOT`` attribute on the class.
    """
    #: The text on the tab. If it is the same as the tab class name capitalized, can be omitted
    TAB_NAME = None

    #: Locator of the Tab selector
    TAB_LOCATOR = ParametrizedLocator(
        './/ul[contains(@class, "nav-tabs")]/li[./a[normalize-space(.)={@tab_name|quote}]]')

    @property
    def tab_name(self):
        return self.TAB_NAME or type(self).__name__.capitalize()

    def is_active(self):
        return 'active' in self.parent_browser.classes(self.TAB_LOCATOR)

    def is_disabled(self):
        return 'disabled' in self.parent_browser.classes(self.TAB_LOCATOR)

    @property
    def is_displayed(self):
        return self.parent_browser.is_displayed(self.TAB_LOCATOR)

    def click(self):
        return self.parent_browser.click(self.TAB_LOCATOR)

    def select(self):
        if not self.is_active():
            if self.is_disabled():
                raise ValueError(
                    'The tab {} you are trying to select is disabled'.format(self.tab_name))
            self.logger.info('opened the tab %s', self.tab_name)
            self.click()

    def child_widget_accessed(self, widget):
        # Select the tab
        self.select()

    def __repr__(self):
        return '<Tab {!r}>'.format(self.tab_name)


class GenericTabWithDropdown(Tab):
    """Tab with a dropdown. Variant that always takes the sub item name in the select().

    Does not support automatic reveal of the tab upon access as the default dropdown item is not
    specified.
    """
    def is_dropdown(self):
        return 'dropdown' in self.parent_browser.classes(self.TAB_LOCATOR)

    def is_open(self):
        return 'open' in self.parent_browser.classes(self.TAB_LOCATOR)

    def open(self):
        if not self.is_open():
            self.logger.info('opened the tab %s', self.tab_name)
            self.click()

    def close(self):
        if self.is_open():
            self.logger.info('closed the tab %s', self.tab_name)
            self.click()

    def select(self, sub_item):
        if not self.is_dropdown():
            raise TypeError('{} is not a tab with dropdown and CHECK_IF_DROPDOWN is True')
        self.open()
        parent = self.parent_browser.element(self.TAB_LOCATOR)
        self.logger.info('clicking the sub-item %r', sub_item)
        self.parent_browser.click(
            './ul/li[normalize-space(.)={}]'.format(quote(sub_item)),
            parent=parent)

    def child_widget_accessed(self, widget):
        """Nothing. Since we don't know which sub_item."""

    def __repr__(self):
        return '<TabWithDropdown {!r}>'.format(self.tab_name)


class TabWithDropdown(GenericTabWithDropdown):
    """Tab with the dropdown and its selection item set so child_widget_accessed work as usual."""
    #: Specify the dropdown item here
    SUB_ITEM = None

    def select(self):
        return super(TabWithDropdown, self).select(self.SUB_ITEM)

    def child_widget_accessed(self, widget):
        # Redefine it back like in Tab since TabWithDropdown removes it
        self.select()

    def __repr__(self):
        return '<TabWithDropdownDefault {!r}>'.format(self.tab_name)


class Accordion(View, ClickableMixin):
    """Bootstrap/Patternfly accordions.

    They are like views that contain widgets. If a widget is accessed in the accordion, the
    accordion makes sure that it is open.

    You need to set the ``ACCORDION_NAME`` to correspond with the text in the accordion.
    If the accordion title is just a capitalized version of the accordion class name, you do not
    need to set the ``ACCORDION_NAME``.

    If the accordion is in an exotic location, you also have to change the ``ROOT``.

    Accordions can contain trees. Basic ``TREE_LOCATOR`` is tuned after ManageIQ so if your UI has a
    different structure, you should change this locator accordingly.
    """
    ACCORDION_NAME = None
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "panel-group")]/div[contains(@class, "panel") and '
        './div/h4/a[normalize-space(.)={@accordion_name|quote}]]')
    TREE_LOCATOR = '|'.join([
        './/miq-tree-view',
        './/div[contains(@class, "treeview") and ./ul]',
        './/div[./ul[contains(@class, "dynatree-container")]]'])
    HEADER_LOCATOR = './div/h4/a'

    @property
    def accordion_name(self):
        return self.ACCORDION_NAME or type(self).__name__.capitalize()

    @property
    def is_opened(self):
        attr = self.browser.get_attribute('aria-expanded', self)
        if attr is None:
            # Try other way
            panel = self.browser.element('./div[contains(@class, "panel-collapse")]')
            classes = self.browser.classes(panel)
            return 'collapse' in classes and 'in' in classes
        else:
            return attr.lower().strip() == 'true'

    @property
    def is_closed(self):
        return not self.is_opened

    def click(self):
        """Override Clickable's click."""
        self.browser.click(self.HEADER_LOCATOR)

    def open(self):
        if self.is_closed:
            self.logger.info('opening')
            self.click()
            try:
                wait_for(lambda: self.is_opened, delay=0.1, num_sec=3)
            except TimedOutError:
                self.logger.warning('Could not open the accordion, trying clicking again')
                # Workaround stupid pages, perhaps we put a try mechanism in here
                if self.is_closed:
                    self.click()
                    try:
                        wait_for(lambda: self.is_opened, delay=0.1, num_sec=3)
                    except TimedOutError:
                        self.logger.error('Could not open the accordion')
                        raise Exception('Could not open accordion {}'.format(self.accordion_name))

    def close(self):
        if self.is_opened:
            self.logger.info('closing')
            self.click()

    def child_widget_accessed(self, widget):
        # Open the Accordion
        self.open()

    def read(self):
        if self.is_closed:
            do_not_read_this_widget()
        return super(Accordion, self).read()

    @cached_property
    def tree_id(self):
        try:
            el = self.browser.element(self.TREE_LOCATOR)
        except NoSuchElementException:
            raise AttributeError('No tree in the accordion {}'.format(self.accordion_name))
        else:
            return self.browser.get_attribute('id', el) or self.browser.get_attribute('name', el)

    def __repr__(self):
        return '<Accordion {!r}>'.format(self.accordion_name)


class BootstrapSelect(Widget, ClickableMixin):
    """This class represents the Bootstrap Select widget.

    Args:
        id: id of the select, that is the ``data-id`` attribute on the ``button`` tag.
        name: name of the select tag
        locator: If none of above apply, you can also supply a full locator.
        can_hide_on_select: Whether the select can hide after selection, important for
            :py:meth:`close` to work properly.
    """
    Option = namedtuple("Option", ["text", "value"])
    LOCATOR_START = './/div[contains(@class, "bootstrap-select")]'
    ROOT = ParametrizedLocator('{@locator}')
    BY_VISIBLE_TEXT = '//div/ul/li/a[./span[contains(@class, "text") and normalize-space(.)={}]]'
    BY_PARTIAL_VISIBLE_TEXT = (
        '//div/ul/li/a[./span[contains(@class, "text") and contains(normalize-space(.), {})]]')

    def __init__(
            self, parent, id=None, name=None, locator=None, can_hide_on_select=False, logger=None):
        Widget.__init__(self, parent, logger=logger)
        if id is not None:
            self.locator = self.LOCATOR_START + '/button[normalize-space(@data-id)={}]/..'.format(
                quote(id))
        elif name is not None:
            self.locator = self.LOCATOR_START + '/select[normalize-space(@name)={}]/..'.format(
                quote(name))
        elif locator is not None:
            self.locator = locator
        else:
            raise TypeError('You need to specify either, id, name or locator for BootstrapSelect')
        self.id = id
        self.can_hide_on_select = can_hide_on_select

    @property
    def is_open(self):
        try:
            return 'open' in self.browser.classes(self)
        except StaleElementReferenceException:
            self.logger.warning(
                'Got a StaleElementReferenceException in .is_open, but ignoring. Returned False.')
            return False

    @property
    def is_multiple(self):
        return 'show-tick' in self.browser.classes(self)

    def open(self):
        if not self.is_open:
            self.click()
            self.logger.debug('opened')

    def close(self):
        try:
            if self.is_open:
                self.click()
                self.logger.debug('closed')
        except NoSuchElementException:
            if self.can_hide_on_select:
                self.logger.info('While closing %r it disappeared, but ignoring.', self)
            else:
                raise

    def select_by_visible_text(self, *items):
        """Selects items in the select.

        Args:
            *items: Items to be selected. If the select does not support multiple selections and you
                pass more than one item, it will raise an exception. If you want to select using
                partial match, use the :py:class:`BootstrapSelect.partial` to wrap the value.
        """
        if len(items) > 1 and not self.is_multiple:
            raise ValueError(
                'The BootstrapSelect {} does not allow multiple selections'.format(self.locator))
        self.open()
        for item in items:
            if isinstance(item, partial_match):
                item = item.item
                self.logger.info('selecting by partial visible text: %r', item)
                try:
                    self.browser.click(
                        self.BY_PARTIAL_VISIBLE_TEXT.format(quote(item)), parent=self,
                        force_scroll=True)
                except NoSuchElementException:
                    try:
                        # Added this as for some views(some tags pages) dropdown is separated from
                        # button and doesn't have exact id or name
                        self.browser.click(
                            self.BY_PARTIAL_VISIBLE_TEXT.format(quote(item)), force_scroll=True)
                    except NoSuchElementException:
                        raise SelectItemNotFound(widget=self, item=item,
                                                 options=[opt.text for opt in self.all_options])
            else:
                self.logger.info('selecting by visible text: %r', item)
                try:
                    self.browser.click(self.BY_VISIBLE_TEXT.format(quote(item)),
                                       parent=self, force_scroll=True)
                except NoSuchElementException:
                    try:
                        # Added this as for some views(some tags pages) dropdown is separated from
                        # button and doesn't have exact id or name
                        self.browser.click(self.BY_VISIBLE_TEXT.format(quote(item)),
                                           force_scroll=True)
                    except NoSuchElementException:
                        raise SelectItemNotFound(widget=self, item=item,
                                                 options=[opt.text for opt in self.all_options])
        self.close()

    @property
    def all_selected_options(self):
        return [
            self.browser.text(e)
            for e in self.browser.elements(
                './div/ul/li[contains(@class, "selected")]/a/span[contains(@class, "text")]',
                parent=self)]

    @property
    def all_options(self):
        b = self.browser
        return [
            self.Option(
                b.text(b.element('.//span[contains(@class, "text")]', parent=e)),
                e.get_attribute("data-original-index")
            )
            for e in b.elements('./div/ul/li', parent=self)
        ]

    @property
    def selected_option(self):
        return self.all_selected_options[0]

    def read(self):
        if self.is_multiple:
            return self.all_selected_options
        else:
            return self.selected_option

    def fill(self, items):
        if not isinstance(items, (list, tuple, set)):
            items = {items}
        elif not isinstance(items, set):
            items = set(items)

        if set(self.all_selected_options) == items:
            return False
        else:
            self.select_by_visible_text(*items)
            return True

    def __repr__(self):
        return '{}(locator={!r})'.format(type(self).__name__, self.locator)


class BootstrapTreeview(Widget):
    """A class representing the Bootstrap treeview used in newer builds.

    Implements ``expand_path``, ``click_path``, ``read_contents``. All are implemented in manner
    very similar to the original :py:class:`Tree`.

    You don't have to specify the ``tree_id`` if the hosting object implements ``tree_id``.

    Args:
        tree_id: Id of the tree, the closest div or ``miq-tree-view`` to the root ``ul`` element.
    """
    ROOT = ParametrizedLocator('|'.join([
        './/miq-tree-view[@name={@tree_id|quote}]/div',
        './/div[@id={@tree_id|quote}]'
    ]))
    ROOT_ITEM = './ul/li[1]'
    ROOT_ITEMS = './ul/li[not(./span[contains(@class, "indent")])]'
    ROOT_ITEMS_WITH_TEXT = (
        './ul/li[not(./span[contains(@class, "indent")]) and contains(normalize-space(.), {text})]')
    SELECTED_ITEM = './ul/li[contains(@class, "node-selected")]'
    CHILD_ITEMS = (
        './ul/li[starts-with(@data-nodeid, {id}) and not(@data-nodeid={id})'
        ' and count(./span[contains(@class, "indent")])={indent}]')
    CHILD_ITEMS_TEXT = (
        './ul/li[starts-with(@data-nodeid, {id}) and not(@data-nodeid={id})'
        ' and (contains(@title, {text}) or contains(normalize-space(.), {text}))'
        ' and count(./span[contains(@class, "indent")])={indent}]')
    ITEM_BY_NODEID = './ul/li[@data-nodeid={}]'
    IS_EXPANDABLE = './span[contains(@class, "expand-icon")]'
    IS_EXPANDED = './span[contains(@class, "expand-icon") and contains(@class, "fa-angle-down")]'
    IS_LOADING = './span[contains(@class, "expand-icon") and contains(@class, "fa-spinner")]'
    INDENT = './span[contains(@class, "indent")]'

    def __init__(self, parent, tree_id=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self._tree_id = tree_id

    @property
    def tree_id(self):
        """If you did not specify the tree_id when creating the tree, it will try to pull it out of
        the parent object.

        This is useful if some kinds of objects contain trees regularly, then the definition gets
        simpler and the tree id is not neded to be specified.
        """
        if self._tree_id is not None:
            return self._tree_id
        else:
            try:
                return self.parent.tree_id
            except AttributeError:
                raise NameError(
                    'You have to specify tree_id to BootstrapTreeview if the parent object does '
                    'not implement .tree_id!')

    def image_getter(self, item):
        """Look up the image that is hidden in the style tag or as a tag.

        Returns:
            The name of the image without the hash, path and extension.
        """
        try:
            image_node = self.browser.element(
                './span[contains(@class, "node-image") or contains(@class, "node-icon")]',
                parent=item)
        except NoSuchElementException:
            self.logger.warning('No image tag found')
            return None
        style = self.browser.get_attribute('style', image_node)
        if style:
            image_href = re.search(r'url\("([^"]+)"\)', style).groups()[0]
            try:
                return re.search(r'/([^/]+)-[0-9a-f]+\.(?:png|svg)$', image_href).groups()[0]
            except AttributeError:
                return None
        else:
            classes = self.browser.classes(image_node)
            try:
                return [c for c in classes if c.startswith(
                    ('fa-', 'product-', 'vendor-', 'pficon-')
                )][0]
            except IndexError:
                return None

    def read(self):
        return self.currently_selected

    def fill(self, value):
        if self.currently_selected == value:
            return False
        self.click_path(*value)
        return True

    @property
    def currently_selected(self):
        if self.selected_item is not None:
            nodeid = self.get_nodeid(self.selected_item).split('.')
            root_id_len = len(self.get_nodeid(self.root_item).split('.'))
            result = []
            for end in range(root_id_len, len(nodeid) + 1):
                current_nodeid = '.'.join(nodeid[:end])
                text = self.browser.text(self.get_item_by_nodeid(current_nodeid))
                result.append(text)
            return result
        else:
            return None

    @property
    def root_item_count(self):
        return len(self.root_items)

    @property
    def root_items(self):
        return self.browser.elements(self.ROOT_ITEMS, parent=self)

    @property
    def root_item(self):
        if self.root_item_count == 1:
            return self.browser.element(self.ROOT_ITEM, parent=self)
        else:
            return None

    @property
    def selected_item(self):
        try:
            result = self.browser.element(self.SELECTED_ITEM, parent=self)
        except NoSuchElementException:
            result = None
        return result

    def indents(self, item):
        return len(self.browser.elements(self.INDENT, parent=item))

    def is_expandable(self, item):
        return bool(self.browser.elements(self.IS_EXPANDABLE, parent=item))

    def is_expanded(self, item):
        return bool(self.browser.elements(self.IS_EXPANDED, parent=item))

    def is_loading(self, item):
        return bool(self.browser.elements(self.IS_LOADING, parent=item))

    def is_collapsed(self, item):
        return not self.is_expanded(item)

    def is_selected(self, item):
        return 'node-selected' in self.browser.classes(item)

    def get_nodeid(self, item):
        return self.browser.get_attribute('data-nodeid', item)

    def get_expand_arrow(self, item):
        return self.browser.element(self.IS_EXPANDABLE, parent=item)

    def child_items(self, item):
        """Returns all child items of given item.

        Args:
            item: WebElement of the node.

        Returns:
            List of *all* child items of the item.
        """
        if item is not None:
            nodeid = quote(self.get_nodeid(item))
            node_indents = self.indents(item)
            return self.browser.elements(
                self.CHILD_ITEMS.format(id=nodeid, indent=node_indents + 1), parent=self)
        else:
            return self.browser.elements(self.ROOT_ITEMS, parent=self)

    def child_items_with_text(self, item, text):
        """Returns all child items of given item that contain the given text.

        Args:
            item: WebElement of the node.
            text: Text to be matched

        Returns:
            List of all child items of the item *that contain the given text*.
        """

        text = quote(text)
        if item is not None:
            nodeid = quote(self.get_nodeid(item))
            node_indents = self.indents(item)
            return self.browser.elements(
                self.CHILD_ITEMS_TEXT.format(id=nodeid, text=text, indent=node_indents + 1),
                parent=self)
        else:
            return self.browser.elements(self.ROOT_ITEMS_WITH_TEXT.format(text=text), parent=self)

    def get_item_by_nodeid(self, nodeid):
        nodeid_q = quote(nodeid)
        try:
            return self.browser.element(self.ITEM_BY_NODEID.format(nodeid_q), parent=self)
        except NoSuchElementException:
            raise CandidateNotFound({
                'message':
                    'Could not find the item with nodeid {} in Bootstrap tree {}'.format(
                        nodeid,
                        self.tree_id),
                'path': '',
                'cause': ''})

    def expand_node(self, nodeid):
        """Expands a node given its nodeid. Must be visible

        Args:
            nodeid: ``nodeId`` of the node

        Returns:
            ``True`` if it was possible to expand the node, otherwise ``False``.
        """
        node = self.get_item_by_nodeid(nodeid)
        if not self.is_expandable(node):
            self.logger.debug('Node %s not expandable on tree %s', nodeid, self.tree_id)
            return False
        if self.is_collapsed(node):
            self.logger.debug('Expanding collapsed node %s on tree %s', nodeid, self.tree_id)
            arrow = self.get_expand_arrow(node)
            self.browser.click(arrow)
            time.sleep(0.1)
            wait_for(
                lambda: not self.is_loading(self.get_item_by_nodeid(nodeid)),
                delay=0.2, num_sec=30)
            wait_for(
                lambda: self.is_expanded(self.get_item_by_nodeid(nodeid)),
                delay=0.2, num_sec=10)
        else:
            self.logger.debug('Node %s already expanded on tree %s', nodeid, self.tree_id)
        return True

    def collapse_node(self, nodeid):
        """Collapses a node given its nodeid. Must be visible

        Args:
            nodeid: ``nodeId`` of the node

        Returns:
            ``True`` if it was possible to expand the node, otherwise ``False``.
        """
        node = self.get_item_by_nodeid(nodeid)
        if not self.is_expandable(node):
            self.logger.debug('Node %s not expandable on tree %s', nodeid, self.tree_id)
            return False
        if self.is_expanded(node):
            self.logger.debug('Collapsing expanded node %s on tree %s', nodeid, self.tree_id)
            arrow = self.get_expand_arrow(node)
            self.browser.click(arrow)
            time.sleep(0.1)
            wait_for(
                lambda: self.is_collapsed(self.get_item_by_nodeid(nodeid)),
                delay=0.2, num_sec=10)
        else:
            self.logger.debug('Node %s already collapsed on tree %s', nodeid, self.tree_id)
        return True

    def _process_step(self, step):
        """Steps can be plain strings or tuples when matching images"""
        if isinstance(step, VersionPick):
            # Version pick passed, coerce it ...
            step = step.pick(self.browser.product_version)

        if isinstance(step, tuple):
            image = step[0]
            step = step[1]
            if isinstance(step, VersionPick):
                # Version pick passed, coerce it ...
                step = step.pick(self.browser.product_version)
        else:
            image = None
        if not isinstance(step, (str, Pattern)):
            step = str(step)
        return image, step

    @staticmethod
    def _repr_step(image, step):
        if isinstance(step, Pattern):
            # Make it look like r'pattern'
            step_repr = 'r' + re.sub(r'^[^"\']', '', repr(step.pattern))
        else:
            step_repr = step
        if image is None:
            return step_repr
        else:
            return '{}[{}]'.format(step_repr, image)

    def pretty_path(self, path):
        return '/'.join(self._repr_step(*self._process_step(step)) for step in path)

    def validate_node(self, node, matcher, image):
        """Helper method that matches nodes by given conditions.

        Args:
            node: Node that is matched
            matcher: If it is an instance of regular expression, that one is used, otherwise
                equality comparison is used. Against item name.
            image: If not None, then after the matcher matches, this will do an additional check for
                the image name

        Returns:
            A :py:class:`bool` if the node is correct or not.
        """
        text = self.browser.text(node)
        if isinstance(matcher, Pattern):
            match = matcher.match(text) is not None
        else:
            match = matcher == text
        if not match:
            return False
        if image is not None and self.image_getter(node) != image:
            return False
        return True

    def expand_path(self, *path, **kwargs):
        """Expands given path and returns the leaf node.

        The path items can be plain strings. In that case, exact string matching happens. Path items
        can also be compiled regexps, where the ``match`` method is used to determine if the node
        is the one we want. And finally, the path items can be 2-tuples, where the second item can
        be the string or regular expression and the first item is the image to be matched using
        :py:meth:`image_getter` method.

        Args:
            *path: The path (explained above)

        Returns:
            The leaf WebElement.

        Raises:
            :py:class:`CandidateNotFound` when the node is not found in the tree.
        """
        self.browser.plugin.ensure_page_safe()
        self.logger.info('Expanding path %s on tree %s', self.pretty_path(path), self.tree_id)
        node = self.root_item
        if node is not None:
            step = path[0]
            steps_tried = [step]
            image, step = self._process_step(step)
            path = path[1:]
            self.logger.debug('Validating presence of %r as the root item of the tree', step)
            if not self.validate_node(node, step, image):
                raise CandidateNotFound({
                    'message':
                        'Could not find the item {} in Bootstrap tree {}'.format(
                            self.pretty_path(steps_tried),
                            self.tree_id),
                    'path': path,
                    'cause': 'Root node did not match {}'.format(self._repr_step(image, step))})
        else:
            steps_tried = []
        for step in path:
            steps_tried.append(step)
            self.logger.debug('Expanding %r', steps_tried)
            image, step = self._process_step(step)
            if node is not None and not self.expand_node(self.get_nodeid(node)):
                raise CandidateNotFound({
                    'message':
                        'Could not find the item {} in Bootstrap tree {}'.format(
                            self.pretty_path(steps_tried),
                            self.tree_id),
                    'path': path,
                    'cause': 'Could not expand the {} node'.format(self._repr_step(image, step))})
            if isinstance(step, str):
                # To speed up the search when having a string to match, pick up items with that text
                child_items = self.child_items_with_text(node, step)
            else:
                # Otherwise we need to go through all of them.
                child_items = self.child_items(node)
            for child_item in child_items:
                if self.validate_node(child_item, step, image):
                    node = child_item
                    break
            else:
                raise CandidateNotFound({
                    'message':
                        'Could not find the item {} in Bootstrap tree {}'.format(
                            self.pretty_path(steps_tried),
                            self.tree_id),
                    'path': path,
                    'cause': 'Was not found in {}'.format(
                        self._repr_step(*self._process_step(steps_tried[-2])))})

        return node

    def click_path(self, *path, **kwargs):
        """Expands the path and clicks the leaf node.

        See :py:meth:`expand_path` for more informations about synopsis.
        """
        node = self.expand_path(*path, **kwargs)
        self.logger.info('clicking node %r', path[-1])
        self.browser.click(node)
        return node

    def has_path(self, *path, **kwargs):
        """Determine if the path exists in the tree.

        See :py:meth:`expand_path` for more information about the arguments.
        """
        try:
            self.expand_path(*path, **kwargs)
            return True
        except CandidateNotFound:
            return False

    def read_contents(self, nodeid=None, include_images=False, collapse_after_read=False):
        """Reads the contents of the tree into a tree structure of strings and lists.

        This method is called recursively.

        Args:
            nodeid: id of the node where the process should start from.
            include_images: If True, the values will be tuples where first item will be the image
                name and the second item the item name. If False then the values are just the item
                names.
            collapse_after_read: If True, then every branch that was read completely gets collapsed.

        Returns:
            :py:class:`list`
        """
        if nodeid is None and self.root_item is not None:
            return self.read_contents(
                nodeid=self.get_nodeid(self.root_item),
                include_images=include_images,
                collapse_after_read=collapse_after_read)

        item = self.get_item_by_nodeid(nodeid)
        self.expand_node(nodeid)
        result = []

        for child_item in self.child_items(item):
            result.append(
                self.read_contents(
                    nodeid=self.get_nodeid(child_item),
                    include_images=include_images,
                    collapse_after_read=collapse_after_read))

        if collapse_after_read:
            self.collapse_node(nodeid)

        if include_images:
            this_item = (self.image_getter(item), self.browser.text(item))
        else:
            this_item = self.browser.text(item)
        if result:
            return [this_item, result]
        else:
            return this_item

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.tree_id)


class CheckableBootstrapTreeview(BootstrapTreeview):
    """ Checkable variation of CFME Tree. This widget not only expand a tree for a provided path,
    but also checks a checkbox.
    """

    IS_CHECKABLE = './span[contains(@class, "check-icon")]'
    IS_CHECKED = './span[contains(@class, "check-icon") and contains(@class, "fa-check-square-o")]'

    CheckNode = namedtuple('CheckNode', ['path'])
    UncheckNode = namedtuple('UncheckNode', ['path'])

    def is_checkable(self, item):
        return bool(self.browser.elements(self.IS_CHECKABLE, parent=item))

    def is_checked(self, item):
        return bool(self.browser.elements(self.IS_CHECKED, parent=item))

    def check_uncheck_node(self, check, *path, **kwargs):
        leaf = self.expand_path(*path, **kwargs)
        if not self.is_checkable(leaf):
            raise TypeError('Item with path {} in {} is not checkable'.format(
                self.pretty_path(path), self.tree_id))
        checked = self.is_checked(leaf)
        if checked != check:
            self.logger.info('%s %r', 'Checking' if check else 'Unchecking', path[-1])
            self.browser.click(self.IS_CHECKABLE, parent=leaf)
            return True
        else:
            return False

    def check_node(self, *path, **kwargs):
        """Expands the passed path and checks a checkbox that is located at the node."""
        return self.check_uncheck_node(True, *path, **kwargs)

    def uncheck_node(self, *path, **kwargs):
        """Expands the passed path and unchecks a checkbox that is located at the node."""
        return self.check_uncheck_node(False, *path, **kwargs)

    def node_checked(self, *path, **kwargs):
        """Check if a checkbox is checked on the node in that path."""
        leaf = self.expand_path(*path, **kwargs)
        if not self.is_checkable(leaf):
            return False
        return self.is_checked(leaf)

    def fill(self, node):
        """
        Args:
            node: CheckNode/UncheckNode namedtuple with path

        Returns:
            boolean for whether or not the path changed
        """
        if not isinstance(node, (self.CheckNode, self.UncheckNode)):
            raise ValueError('node in must be CheckNode or UncheckNode namedtuple')
        return self.check_uncheck_node(isinstance(node, self.CheckNode), *node.path)

    def read(self):
        do_not_read_this_widget()


class Dropdown(Widget):
    """Represents the Patternfly/Bootstrap dropdown.

    Args:
        text: Text of the button, can be the inner text or the title attribute.
    """
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "dropdown") and ./button[normalize-space(.)={@text|quote} or '
        'normalize-space(@title)={@text|quote}]]')
    BUTTON_LOCATOR = './button'
    ITEMS_LOCATOR = './ul/li/a'
    ITEM_LOCATOR = './ul/li/a[normalize-space(.)={}]'

    def __init__(self, parent, text, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.text = text

    @property
    def is_enabled(self):
        """Returns if the toolbar itself is enabled and therefore interactive."""
        button = self.browser.element(self.BUTTON_LOCATOR, parent=self)
        return 'disabled' not in self.browser.classes(button)

    def _verify_enabled(self):
        if not self.is_enabled:
            raise DropdownDisabled('Dropdown "{}" is not enabled'.format(self.text))

    @property
    def currently_selected(self):
        """Returns the currently selected item text."""
        return self.browser.text(self.BUTTON_LOCATOR, parent=self)

    def read(self):
        return self.currently_selected

    @property
    def is_open(self):
        return 'open' in self.browser.classes(self)

    def open(self):
        self._verify_enabled()
        if not self.is_open:
            self.browser.click(self)

    def close(self, ignore_nonpresent=False):
        """Close the dropdown

        Args:
            ignore_nonpresent: Will ignore exceptions due to disabled or missing dropdown
        """
        try:
            self._verify_enabled()
            if self.is_open:
                self.browser.click(self)
        except (NoSuchElementException, DropdownDisabled):
            if ignore_nonpresent:
                self.logger.info('%r hid so it was not possible to close it. But ignoring.', self)
            else:
                raise

    @property
    def items(self):
        """Returns a list of all dropdown items as strings."""
        return [
            self.browser.text(el) for el in self.browser.elements(self.ITEMS_LOCATOR, parent=self)]

    def has_item(self, item):
        """Returns whether the items exists.

        Args:
            item: item name

        Returns:
            Boolean - True if enabled, False if not.
        """
        return item in self.items

    def item_element(self, item):
        """Returns a WebElement for given item name."""
        try:
            return self.browser.element(self.ITEM_LOCATOR.format(quote(item)), parent=self)
        except NoSuchElementException:
            try:
                items = self.items
            except NoSuchElementException:
                items = []
            if items:
                items_string = 'These items are present: {}'.format('; '.join(items))
            else:
                items_string = 'The dropdown is probably not present'
            raise DropdownItemNotFound('Item {!r} not found. {}'.format(item, items_string))

    def item_title(self, item):
        el = self.item_element(item)
        li = self.browser.element('./a', parent=el)
        return self.browser.get_attribute('title', li)

    def item_enabled(self, item):
        """Returns whether the given item is enabled.

        Args:
            item: Name of the item.

        Returns:
            Boolean - True if enabled, False if not.
        """
        self._verify_enabled()
        el = self.item_element(item)
        li = self.browser.element('..', parent=el)
        return 'disabled' not in self.browser.classes(li)

    def item_select(self, item, handle_alert=None):
        """Opens the dropdown and selects the desired item.

        Args:
            item: Item to be selected
            handle_alert: How to handle alerts. None - no handling, True - confirm, False - dismiss.
        """
        self.logger.info('Selecting %r', item)
        try:
            self.open()
            if not self.item_enabled(item):
                reason = self.item_title(item)
                raise DropdownItemDisabled(
                    'Item "{item}" of dropdown "{dropdown}" is disabled due to \n'
                    '{reason}'
                    'The following items are available: {available}'
                    .format(
                        item=item,
                        dropdown=self.text,
                        reason=reason,
                        available=';'.join(self.items)
                    )
                )
            self.browser.click(self.item_element(item), ignore_ajax=handle_alert is not None)
            if handle_alert is not None:
                self.browser.handle_alert(cancel=not handle_alert, wait=10.0)
                self.browser.plugin.ensure_page_safe()
        finally:
            try:
                self.close(ignore_nonpresent=True)
            except UnexpectedAlertPresentException:
                self.logger.warning('There is an unexpected alert present.')
                pass

    @property
    def hover(self):
        # title will act as hover for disabled Dropdown
        return self.browser.element(self.BUTTON_LOCATOR).get_attribute("title")

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.text)


class SelectorDropdown(Dropdown):
    """A variant of :py:class:`Dropdown` which allows selecting values.

    Unlike :py:class:`Dropdown` it supports read and fill because it usually does not change pages
    like ordinary dropdown does.

    Args:
        button_attr: Name of the attribute matched on the button inside the dropdown div
        button_attr_value: The value to match on that attr
    """
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "dropdown") and ./button[@{@b_attr}={@b_attr_value|quote}]]')

    def __init__(self, parent, button_attr, button_attr_value, logger=None):
        # Skipping Dropdown init because it has nothing interesting for us
        Widget.__init__(self, parent, logger=logger)
        self.b_attr = button_attr
        self.b_attr_value = button_attr_value

    def item_select(self, item, *args, **kwargs):
        super(SelectorDropdown, self).item_select(item, *args, **kwargs)
        wait_for(lambda: self.currently_selected == item, num_sec=3, delay=0.2)

    def fill(self, value):
        if value == self.currently_selected:
            return False
        self.item_select(value)
        return True

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.b_attr, self.b_attr_value)


class BootstrapSwitch(BaseInput):
    """ represents checkbox like switch control. Widgetastic checkbox doesn't work right for
    this control.
    .. code-block:: python

        switch = BootstrapSwitch(id="default_tls_verify"')
        switch.fill(True)
        switch.read()
    """

    PARENT = './..'
    ROOT = ParametrizedLocator(
        '|'.join([
            './/div/text()[normalize-space(.)={@label|quote}]/'
            'preceding-sibling::div[1]//'
            'div[contains(@class, "bootstrap-switch-container")]'
            '{@input}',
            './/div/div[contains(@class, "bootstrap-switch-container")]'
            '{@input}']))

    def __init__(self, parent, id=None, name=None, label=None, logger=None):
        self._label = label
        if not (id or name or self._label):
            raise ValueError('either id, name or label should be present')
        elif name is not None and self._label is None:
            self.input = '//input[@name={}]'.format(quote(name))
            self.label = ''
        elif id is not None and self._label is None:
            self.input = '//input[@id={}]'.format(quote(id))
            self.label = ''
        elif self._label is not None and name is None and id is None:
            self.input = '//input'
            self.label = self._label
        else:
            raise ValueError('label, id and name cannot be used together')

        BaseInput.__init__(self, parent, locator=self.ROOT, logger=logger)

    @property
    def selected(self):
        # it seems there is a bug in patternfly lib because in some cases
        # BootstrapSwitch->input.checked returns False when control is definitely checked
        classes = self.browser.classes(self)
        if 'ng-not-empty' in classes:
            return True
        elif 'ng-empty' in classes:
            return False
        else:
            return self.browser.is_selected(self)

    @property
    def is_displayed(self):
        return self.browser.is_displayed(locator=self.PARENT, parent=self)

    @property
    def _clickable_el(self):
        """input itself is not clickable because it's hidden, instead we should click on a parent
        element e.g. div.

        Returns: selenium webelement
        """
        return self.browser.element(parent=self, locator=self.PARENT)

    def fill(self, value):
        value = bool(value)
        current_value = self.selected
        if value == current_value:
            return False
        else:
            self.browser.click(self._clickable_el)
            if self.selected != value:
                raise WidgetOperationFailed(
                    'Failed to set the bootstrap switch to requested value.')
            return True

    def read(self):
        return self.selected


class AboutModal(Widget):
    """
    Represents the patternfly about modal

    Provides a close method
    """
    # ROOT_LOC only used when id is not passed to constructor
    ROOT_LOC = ('//div[contains(@class, "modal") and contains(@class, "fade") '
                'and .//div[contains(@class, "about-modal-pf")]]')
    CLOSE_LOC = './/div[@class="modal-header"]/button[@class="close" and @data-dismiss="modal"]'
    ITEMS_LOC = './/div[@class="modal-body"]/div[@class="product-versions-pf"]/ul/li'
    # These are relative to the <li> elements under ITEMS_LOC above
    LABEL_LOC = './strong'
    # widgets for the title+trademark lines
    TITLE_LOC = './/div[@class="modal-body"]/*[self::h1 or self::h2]'
    TRADEMARK_LOC = './/div[@class="modal-body"]/div[@class="trademark-pf"]'

    def __init__(self, parent, id=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.id = id

    def __locator__(self):
        """If id was passed, parametrize it into a locator, otherwise use ROOT_LOC"""
        if self.id is not None:
            return ('//div[normalize-space(@id)="{}" and '
                    'contains(@class, "modal") and '
                    'contains(@class, "fade") and '
                    './/div[contains(@class, "about-modal-pf")]]'
                    .format(self.id))
        else:
            return self.ROOT_LOC

    @property
    def is_open(self):
        """Is the about modal displayed right now"""
        try:
            return 'in' in self.browser.classes(self)
        except NoSuchElementException:
            return False

    def close(self):
        """Close the modal"""
        self.browser.click(self.CLOSE_LOC, parent=self)

    @property
    def title(self):
        return self.browser.text(self.browser.element(self.TITLE_LOC, parent=self))

    @property
    def trademark(self):
        return self.browser.text(self.browser.element(self.TRADEMARK_LOC, parent=self))

    def items(self):
        """
        Generate a dictionary of key-value pairs of fields and their values
        :return: dictionary of keys matching the bold field labels and their values
        """
        items = {}
        list_elements = self.browser.elements(self.ITEMS_LOC, parent=self)
        for element in list_elements:
            # each list item has a label in a <strong> and the value following
            # can't select this text after the strong via xpath and get an element
            key = self.browser.text(self.LABEL_LOC, parent=element)
            element_text = self.browser.text(element)

            # value will include the label from the <strong> block, parse it out
            items.update({key: element_text.replace(key, '', 1).lstrip()})
        return items


class Modal(View):
    """ Patternfly modal widget

        https://www.patternfly.org/pattern-library/widgets/#modal
    """
    ROOT = ('.//div[contains(@class, "modal") '
            'and contains(@class, "fade") and @role="dialog"]')

    def __init__(self, parent, id=None, logger=None):
        self.id = id
        if id:
            self.ROOT = ParametrizedLocator(
                './/div[normalize-space(@id)={@id|quote} and '
                'contains(@class, "modal") and contains(@class, "fade") '
                'and @role="dialog"]')

        View.__init__(self, parent, logger=logger)

    @property
    def title(self):
        return self.header.title.read()

    @property
    def text(self):
        """ Option for compatibility with selenium alerts """
        return self.title

    @property
    def is_displayed(self):
        """ Is the modal currently open? """
        try:
            return "in" in self.browser.classes(self)
        except NoSuchElementException:
            return False

    def close(self):
        """Close the modal"""
        self.header.close.is_displayed and self.header.close.click()

    @View.nested
    class header(View):  # noqa
        """ The header of the modal """
        ROOT = './/div[@class="modal-header"]'
        close = Text(locator='.//button[@class="close"]')
        title = Text(locator='.//h4[@class="modal-title"]')

    @View.nested
    class body(View):  # noqa
        """ The body of the modal """
        ROOT = './/div[@class="modal-body"]'
        body_text = Text(locator=".//h4")

    @View.nested
    class footer(View):  # noqa
        """ The footer of the modal """
        ROOT = './/div[@class="modal-footer"]'
        dismiss = Button("Cancel")
        accept = Button(classes=Button.PRIMARY)

    def dismiss(self):
        """ Cancel the modal"""
        self.footer.dismiss.click()

    def accept(self):
        """ Submit/Save/Accept/Delete for the modal."""
        self.footer.accept.click()


class BreadCrumb(Widget):
    """ Patternfly BreadCrumb navigation control

    .. code-block:: python

        breadcrumb = BreadCrumb()
        breadcrumb.click_location(breadcrumb.locations[0])
    """
    ROOT = '//ol[contains(@class, "breadcrumb")]'
    ELEMENTS = './/li'
    LINK = './/a'

    def __init__(self, parent, locator=None, logger=None):
        Widget.__init__(self, parent=parent, logger=logger)
        self._locator = locator or self.ROOT

    def __locator__(self):
        return self._locator

    @property
    def _path_elements(self):
        return self.browser.elements(self.ELEMENTS, parent=self)

    @property
    def locations(self):
        return [self.browser.text(loc) for loc in self._path_elements]

    @property
    def active_location(self):
        br = self.browser
        return next(br.text(loc) for loc in self._path_elements if 'active' in br.classes(loc))

    def click_location(self, name, handle_alert=True):
        br = self.browser
        try:
            location = next(loc for loc in self._path_elements if br.text(loc) == name)
        except StopIteration:
            self.logger.exception(f'Given location name [{name}] not found')
            raise WidgetOperationFailed('Unable to click breadcrumb location, location not found')
        result = br.click(br.element(self.LINK, parent=location), ignore_ajax=handle_alert)
        if handle_alert:
            self.browser.handle_alert(wait=2.0, squash=True)
            self.browser.plugin.ensure_page_safe()
        return result

    def read(self):
        """Return the active location of the breadcrumb"""
        return self.active_location


class DatePicker(View):
    """Represents the Bootstrap DatePicker.

      Args:
        name: Name of DatePicker
        id: Id of DatePicker
        locator: If none of the above applies, you can also supply a full locator
        strptime_format: `datetime` module `strptime` format. The default is for `mm/dd/yyyy` but
        the user can overwrite as per widget requirement which should comparable with datetime.

    .. code-block:: python
        date = DatePicker(name='miq_date_1')

        # check readonly or editable
        date.is_readonly
        # fill current date
        date.fill(datetime.now())
        # read selected date for DatePicker
        date.read()
    """
    textbox = TextInput(locator=Parameter('@locator'))

    def __init__(self, parent, id=None, name=None,
                strptime_format='%m/%d/%Y', locator=None, logger=None): # noqa
        View.__init__(self, parent=parent, logger=logger)

        self.strptime_format = strptime_format
        base_locator = './/*[(self::input or self::textarea) and @{}={}]'

        if id:
            self.locator = base_locator.format('id', quote(id))
        elif name:
            self.locator = base_locator.format('name', quote(name))
        elif locator:
            self.locator = locator
        else:
            raise TypeError('You need to specify either, id, name or locator for DatePicker')

    class HeaderView(View):
        prev_button = Text(".//*[contains(@class, 'prev')]")
        next_button = Text(".//*[contains(@class, 'next')]")
        datepicker_switch = Text(".//*[contains(@class, 'datepicker-switch')]")
        _elements = {}

        def select(self, value):
            for el, web_el in self._elements.items():
                if el == value:
                    web_el.click()
                    return True

        @property
        def active(self):
            for el, web_el in self._elements.items():
                if bool(self.browser.classes(web_el) & {'active', 'focused'}):
                    return el

    @View.nested
    class date_pick(HeaderView):    # noqa
        DATES = ".//*[contains(@class, 'datepicker-days')]/table/tbody/tr/td"

        @property
        def _elements(self):
            dates = {}
            for el in self.browser.elements(self.DATES):
                if not bool({'old', 'new', 'disabled'} & self.browser.classes(el)):
                    dates.update({int(el.text): el})
            return dates

    @View.nested
    class month_pick(HeaderView):   # noqa
        MONTHS = ".//*[contains(@class, 'datepicker-months')]/table/tbody/tr/td/*"

        @property
        def _elements(self):
            months = {}
            for el in self.browser.elements(self.MONTHS):
                if not bool({'disabled'} & self.browser.classes(el)):
                    months.update({el.text: el})
            return months

    @View.nested
    class year_pick(HeaderView):    # noqa
        YEARS = ".//*[contains(@class, 'datepicker-years')]/table/tbody/tr/td/*"

        @property
        def _elements(self):
            years = {}
            for el in self.browser.elements(self.YEARS):
                if not bool({'old', 'new', 'disabled'} & self.browser.classes(el)):
                    years.update({int(el.text): el})
            return years

        def _pick(self, value):
            for el, web_el in self._elements.items():
                if el == value:
                    web_el.click()
                    return True

        def select(self, value):
            start_yr, end_yr = [int(item) for item in self.datepicker_switch.read().split('-')]
            if value > end_yr:
                for _ in range(end_yr, value, 10):
                    self.next_button.click()
            elif value < start_yr:
                for _ in range(start_yr, value, -10):
                    self.prev_button.click()
            self._pick(value)

    def read(self):
        """Read the current date form DatePicker

        Returns:
            :py:class:`datetime`
        """
        try:
            return datetime.strptime(self.textbox.value, self.strptime_format)
        except ValueError:
            return None

    def fill(self, value):
        """Fill date to DatePicker

        Args:
           value: datetime object.

        Returns:
            :py:class:`bool`
        """
        current_date = self.read()
        if current_date and value.date() == current_date.date():
            return False

        if not self.readonly:
            date = datetime.strftime(value, self.strptime_format)
            self.textbox.fill(date)
            self.date_pick._elements[self.date_pick.active].click()
            return True
        else:
            self.browser.click(self.textbox)
            self.date_pick.datepicker_switch.click()
            self.month_pick.datepicker_switch.click()
            self.year_pick.select(value=value.year)
            self.month_pick.select(value=value.strftime("%b"))
            self.date_pick.select(value=value.day)
            return True

    @property
    def readonly(self):
        """DatePicker is editable or not

        Returns:
            :py:class:`bool`
        """
        return bool(self.browser.get_attribute('readonly', self.textbox))

    @property
    def date_format(self):
        """DatePicker date format

        Returns:
            :py:class:`str`
        """
        return self.browser.get_attribute('data-date-format', self.textbox)

    @property
    def is_displayed(self):
        """DatePicker displayed or not

        Returns:
            :py:class:`bool`
        """
        return self.browser.is_displayed(self.textbox)


class StatusNotification(Widget):
    """Class for the notification elements that are in aggregate status cards

    Provides some attributes for storing the notification class based on icon constants
    And a click method for those notifications tied to an anchor
    """
    # Notification count will be in anchor with an icon
    ANCHOR = './a'
    TEXT = './*[normalize-space(.)]'

    def __init__(self, parent, note_element, logger):
        Widget.__init__(self, parent=parent, logger=logger)
        self.note_element = note_element

    def __locator__(self):
        return self.note_element

    @property
    def icon(self):
        """Icon constant for the notification span

        Returns:
            None if no icon is found in the title element
            PFIcon constant if icon found
        """
        try:
            return PFIcon.icon_from_element(self.note_element, browser=self.browser)
        except NoSuchElementException:
            return None

    @property
    def text(self):
        """text associated with the notification, likely a count

        Returns:
            None if no text is found in the notification element
            str text from the element
        """
        try:
            return self.browser.text(self.TEXT, parent=self)
        except NoSuchElementException:
            return None

    def read(self):
        """Read the notification attributes and return a dict

        Returns:
            dict containing icon and text attributes
        """
        return {
            'icon': self.icon,
            'text': self.text
        }

    def click(self):
        """Click the anchor for this notification

        Raises:
            NoSuchElementException: when there is no anchor to click
        """
        self.browser.click(self.ANCHOR, parent=self)


class AggregateStatusCard(View):
    """Widget for patternfly aggregate status card, used in dashboard views

    This covers the standard type card
    https://www.patternfly.org/pattern-library/cards/aggregate-status-card/#example-code-1
    """
    # Get the aggregate-status card div, per patternfly reference markup
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "card-pf-aggregate-status") '
        'and not(contains(@class, "card-pf-aggregate-status-mini")) '
        'and h2[contains(@class, "card-pf-title")]'
        '//span[normalize-space(following::text())={@name|quote}]]'
    )

    # count is in span with specific class under main card div
    TITLE = './h2[contains(@class, "card-pf-title")]'
    COUNT = './/span[contains(@class, "card-pf-aggregate-status-count")]'
    TITLE_ANCHOR = '/a'

    BODY = './div[contains(@class, "card-pf-body")]'
    NOTIFICATION = ('./p[contains(@class, "card-pf-aggregate-status-notifications")]'
                    '//span[contains(@class, "card-pf-aggregate-status-notification")]')

    ACTION_ANCHOR = ParametrizedLocator('.//a[@title={@action_title|quote} '
                                        'or @data-original-title={@action_title|quote}]')

    def __init__(self, parent, name, locator=None, action_title=None, logger=None):
        """Constructor, using name, can specify locator

        Args:
            name: string name of the status card, displayed with count in top line
            action_title: title attribute for the anchor of the action link in notification block
                            In the patternfly ref, this is an 'add' action with icon
        """
        Widget.__init__(self, parent=parent, logger=logger)
        self.name = name
        self.locator = locator or self.ROOT
        self.action_title = action_title

    def __locator__(self):
        return self.locator

    @property
    def _title(self):
        """tool for local methods to get the title element"""
        return self.browser.element(self.TITLE, parent=self)

    @property
    def _body(self):
        """tool for local methods to get the body element"""
        return self.browser.element(self.BODY, parent=self)

    @property
    def count(self):
        """count in the title

        Returns:
            None if no count element is found
            int count from the element
        """
        try:
            return int(
                self.browser.text(
                    self.browser.element(self.COUNT, parent=self._title)
                )
            )
        except NoSuchElementException:
            return None

    @property
    def icon(self):
        """icon of the title

        Returns:
            None if no icon is found in the title element
            PFIcon constant if icon found
        """
        try:
            return PFIcon.icon_from_element(element=self._title, browser=self.browser)
        except NoSuchElementException:
            return None

    @property
    def notifications(self):
        """read method for the status notifications in the body of the card

        Returns
            list of notification elements, empty when there are none
        """
        try:
            notes = self.browser.elements(self.NOTIFICATION, parent=self._body)
        except NoSuchElementException:
            return []
        return [
            StatusNotification(parent=self, note_element=note, logger=self.logger)
            for note in notes
        ]

    def read(self):
        items = dict(
            icon=self.icon,
            count=self.count,
            name=self.name
        )
        items.update(
            {
                'notifications': [note.read() for note in self.notifications]
            }
        )
        return items

    def click(self):
        self.click_title()

    def click_title(self):
        self.browser.click(self.TITLE_ANCHOR, parent=self)

    def click_body_action(self):
        if self.action_title:
            self.browser.click(self.ACTION_ANCHOR, parent=self)
        else:
            raise LocatorNotImplemented('No action_title, cannot locate action element for click')


class AggregateStatusMiniCard(AggregateStatusCard):
    """Widget for the mini type of aggregate status card

    slightly different display and locator
    https://www.patternfly.org/pattern-library/cards/aggregate-status-card/#example-code-2
    """
    # TODO testing of parent methods against mini card
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "card-pf-aggregate-status") '
        'and contains(@class, "card-pf-aggregate-status-mini") '
        'and h2[contains(@class, "card-pf-title")]'
        '//span[normalize-space(following::text())={@name|quote}]]'
    )


class Kebab(Widget):
    """Patternfly Kebab menu widget

    Args:
        id: Id of Kebab button
        locator: Kebab button locator
    """

    ROOT = ParametrizedLocator("{@locator}")
    BASE_LOCATOR = ".//div[contains(@class, 'dropdown-kebab-pf') and ./button[@id={}]]"
    UL = './ul[contains(@class, "dropdown-menu")]'
    BUTTON = "./button"
    ITEM = "./ul/li/a[normalize-space(.)={}]"
    ITEMS = "./ul/li/a"

    def __init__(self, parent, id=None, locator=None, logger=None):
        Widget.__init__(self, parent=parent, logger=logger)

        if id:
            self.locator = self.BASE_LOCATOR.format(quote(id))
        elif locator:
            self.locator = locator
        else:
            raise TypeError("You need to specify either id or locator")

    @property
    def is_opened(self):
        """Returns opened state of the kebab."""
        return self.browser.is_displayed(self.UL)

    @property
    def items(self):
        """Lists all items in the kebab.

        Returns:
            :py:class:`list` of :py:class:`str`
        """
        return [self.browser.text(item) for item in self.browser.elements(self.ITEMS)]

    def has_item(self, item):
        """Returns whether the items exists.

        Args:
            item: item name

        Returns:
            Boolean - True if enabled, False if not.
        """
        return item in self.items

    def open(self):
        """Open the kebab"""
        if not self.is_opened:
            self.browser.click(self.BUTTON)

    def close(self):
        """Close the kebab"""
        if self.is_opened:
            self.browser.click(self.BUTTON)

    def item_select(self, item, close=True):
        """Select a specific item from the kebab.

        Args:
            item: Item to be selected.
            close: Whether to close the kebab after selection. If the item is a link, you may want
            to set this to `False`.
        """
        try:
            el = self.browser.element(self.ITEM.format(quote(item)))
            self.open()
            self.parent_browser.click(el)
        finally:
            if close:
                self.close()


class SparkLineChart(Widget, ClickableMixin):
    """Represents the Spark Line Chart from Patternfly (Data Visualization).

    Args:
        id: id of SparkLineChart
        locator: If id not applies, you can also supply a full locator

    .. code-block:: python
        spark_line_chart = SparkLineChart(id="sparklineChart")
    """
    ROOT = ParametrizedLocator("{@locator}")
    BASE_LOCATOR = ".//div[@id={}]"
    # axis event mapping
    RECTS = ".//*[contains(@class, 'c3-event-rects c3-event-rects-single')]//*"
    tooltip = Text(".//div[contains(@class,'c3-tooltip-container')]")

    def __init__(self, parent, id=None, locator=None, logger=None):
        """Create the widget"""
        Widget.__init__(self, parent, logger=logger)
        if id:
            self.locator = self.BASE_LOCATOR.format(quote(id))
        elif locator:
            self.locator = locator
        else:
            raise TypeError("You need to specify either id or locator")

    def read(self):
        """read all data on chart

        Returns:
            :py:class:`list` complete data on chart
        """
        data = []
        for el in self.browser.elements(self.RECTS):
            self.browser.move_to_element(el)
            data.append(self.tooltip.read())
        return data


class SingleLineChart(SparkLineChart):
    """Represents the Single Line Chart from Patternfly (Data Visualization).

    Args:
        id: id of SingleLineChart
        locator: If id not applies, you can also supply a full locator

    .. code-block:: python
        single_line_chart = SingleLineChart(id="singleLineChart")
    """
    X_AXIS = ".//*[contains(@class, 'c3-axis c3-axis-x')]/*[contains(@class, 'tick')]"
    tooltip = Table(locator=".//div[contains(@class,'c3-tooltip-container')]/table")

    @property
    def _elements(self):
        br = self.browser
        return {
            x.get_attribute("textContent"): el
            for (x, el) in zip(br.elements(self.X_AXIS), br.elements(self.RECTS))
        }

    def _get_data(self, elements):
        data = {}
        for el in elements:
            self.tooltip.clear_cache()
            self.browser.move_to_element(el)
            raw_data = {row[0].text: row[1].text for row in self.tooltip.rows()}
            if self.tooltip.headers:
                tooltip_data = {self.tooltip.headers[0]: raw_data}
            else:
                # In the absence of a header, `:` separates x-axis points and values.
                tooltip_data = {
                    h[:-1] if (h[-1] == ":") else h: value for h, value in raw_data.items()
                }
            data.update(tooltip_data)
        return data

    def read(self):
        """read all data on chart

        Returns:
            :py:class:`dict` complete data on chart
        """
        return self._get_data(self._elements.values())

    def get_values(self, x_axis):
        """data for specific x-axis point on chart

        Args:
            x_axis: x-axis point as per chart

        Returns:
            :py:class:`dict` data for selected timestamp
        """
        el = [self._elements.get(x_axis)]
        return self._get_data(el)


class LineChart(SingleLineChart):
    """Represents the Line Chart having legends from Patternfly (Data Visualization).

    Args:
        id: id of LineChart
        locator: If id not applies, you can also supply a full locator

    .. code-block:: python
        line_chart = LineChart(id="lineChart")
    """
    LEGENDS = ".//*[contains(@class, 'c3-legend-item c3-legend-item-')]"

    @property
    def _legends(self):
        return {self.browser.text(leg): leg for leg in self.browser.elements(self.LEGENDS)}

    @property
    def legends(self):
        """ Get all available legends

        Returns:
            :py:class:`list` all available legends
        """
        return list(self._legends.keys())

    def legend_is_displayed(self, leg):
        """ Check legend is available or not on Chart
        Args:
            leg: `str` of legend

        Returns:
            :py:class:`bool` all available legends
        """
        if isinstance(leg, str):
            leg = self._legends.get(leg, None)

        if leg:
            return "c3-legend-item-hidden" not in self.browser.classes(leg)
        else:
            return False

    def hide_all_legends(self):
        """To hide all legends on chart"""
        for legend in self._legends.values():
            if self.legend_is_displayed(legend):
                self.browser.click(legend)

    def display_all_legends(self):
        """To display all legends on chart"""
        for legend in self._legends.values():
            if not self.legend_is_displayed(legend):
                self.browser.click(legend)

    def display_legends(self, *legends):
        """Display one or more legends on chart

        Args:
            legends: One or Multiple legends name
        """
        for legend in legends:
            leg = self._legends.get(legend)
            if not self.legend_is_displayed(leg):
                self.browser.click(leg)

    def hide_legends(self, *legends):
        """Hide one or more legends on chart

        Args:
            legends: One or Multiple legends name
        """
        for legend in legends:
            leg = self._legends.get(legend)
            if self.legend_is_displayed(leg):
                self.browser.click(leg)

    def get_data_for_legends(self, *legends):
        """data for specific legends on chart

        Args:
            legends: one or more legends

        Returns:
            :py:class:`dict` data for selected legends
        """
        self.hide_all_legends()
        self.display_legends(*legends)
        return self._get_data(self._elements.values())

    def read(self):
        """read all data on chart

        Returns:
            :py:class:`dict` complete data on chart
        """
        self.display_all_legends()
        return self._get_data(self._elements.values())


class SingleSplineChart(SingleLineChart):
    """Represents the Single Spline Chart from Patternfly (Data Visualization)."""
    pass


class SplineChart(LineChart):
    """Represents the Spline Chart having legends from Patternfly (Data Visualization)."""
    pass


class BarChart(SingleLineChart):
    """Represents the Vertical/Horizontal Bar Chart from Patternfly (Data Visualization)."""
    pass


class GroupedBarChart(LineChart):
    """Represents the Grouped Vertical/Horizontal/Stacked Bar Chart (Having legends)
    from Patternfly (Data Visualization).
    """
    pass


class ListItem(ParametrizedView):
    """ Basic item object for use with ItemsList"""

    PARAMETERS = ("index",)
    ROOT = ParametrizedLocator(
        './/div[contains(@class,"list-group-item") and position()={index}]'
    )
    DESCRIPTION_LOCATOR = './/span[contains(@class,"description-column")]'
    EXPAND_LOCATOR = './/span[contains(@class,"{}")]'.format(PFIcon.icons.ANGLE_RIGHT)
    COLLAPSE_LOCATOR = './/span[contains(@class,"{}")]'.format(PFIcon.icons.ANGLE_DOWN)

    # note that this has 1-based indexing
    index = Parameter("index")

    # properties
    @property
    def item_list(self):
        return self.parent

    @property
    def description(self):
        desc = self.browser.element(self.DESCRIPTION_LOCATOR, parent=self)
        return self.browser.text(desc)

    # methods
    def open(self):
        expand_arrow = self.browser.element(self.EXPAND_LOCATOR, parent=self)
        self.browser.click(expand_arrow)

    def close(self):
        collapse_arrow = self.browser.element(self.COLLAPSE_LOCATOR, parent=self)
        self.browser.click(collapse_arrow)

    def read(self):
        return self.browser.text(self)


class ItemsList(View):
    """Basic list-view handling class:
    https://www.patternfly.org/pattern-library/content-views/list-view/
    Most functionality is meant to mimic widgetastic's Table class.
    This class is meant to work with an ItemClass that is defined elsewhere. The ItemClass
    is a ParametrizedView that represents a single item in the list-view
    (similar to TableRow and Table). The parameter for the ItemClass is it's index/position in
    the list-view.

    In practice, the ItemClass will be defined within a nested view e.g. in a view class we could
    have:
    .. code-block:: python
        # define a view
        class MyView(BaseLoggedInPage):
            # define the list-view widget that's on this page
            @View.nested
            class item_list(ItemsList):
                # define the item_class that the list-view uses (default is ListItem)
                item_class = ItemClass
                # define a default assoc_column that can be used for filtering
                assoc_column = <assoc_column_str>
            # define whatever else this page has on it ...

    For an example: integration_tests/cfme/control/explorer/alerts.py::MonitorAlertsAllView

    Usage is as follows assuming the list is instantiated as ``view.item_list``:

    .. code-block:: python
        # Access item by position
        view.item_list[0] # => gives first item in list-view
        # Iterate through rows
        for item in view.item_list:
            do_something()
        # You can also filter items in two main ways
        # 1) by an assoc_column that corresponds to an attribute of the item_class e.g.
        item_list = view.item_list
        item_list.assoc_column = 'description' # if assoc_column was not defined in item_list def
        filtered_items = item_list[<desired_description>] # where <desired_description> is a str
        # 2) by key-value pairs
        item_filter = {'description': <desired_description>}
        filtered_items = view.item_list[item_filter]
        # note that filters can also be applied to the items() method
        # e.g.
        filtered_items = view.item_list.items(item_filter)

    Args:
         assoc_column: Name of an attribute/property defined in the item_class
    """

    ROOT = './/div[contains(@class,"list-view-pf-view")]'
    ITEMS = './/div[contains(@class,"list-group-item-header")]'
    item_class = ListItem  # default item_class

    def __init__(self, parent, assoc_column=None, logger=None):
        View.__init__(self, parent, logger=logger)
        self._assoc_column = assoc_column

    def __getitem__(self, item_filter):
        """ allows the ability to directly select AlertItem by a filter with
            item = view.alerts_list[item_filter],
            item_filter can be of type: string, dict, int, or None
        """
        if isinstance(item_filter, int):
            return next(self.items(item_filter))
        elif isinstance(item_filter, str) or isinstance(item_filter, dict) or item_filter is None:
            return self.items(item_filter)
        else:
            raise ValueError("item_filter is of {} but must be of type: "
                             "str, dict, int, or None.".format(type(item_filter)))

    # properties
    @property
    def assoc_column(self):
        return self._assoc_column or 'description'  # note the defualt

    @property
    def item_count(self):
        """ returns how many rows are currently in the table."""
        return len(self.browser.elements(self.ITEMS, parent=self))

    # methods
    def items(self, item_filter=None):
        """ returns a generator for all Items matching the item_filter"""
        start = 1  # start at 1 and not 0 since position() returns 1 as the first index
        stop = self.item_count + 1
        # filter via key, value pair
        if isinstance(item_filter, dict):
            key, value = next(item_filter.items())
            if len(item_filter) > 1:
                self.logger.warning(
                    "List-view filter currently not implemented for dictionaries"
                    "greater than a length of one. Selecting the first key value pair from the dict"
                )
        # filter via string, note the default
        elif isinstance(item_filter, str):
            key = self.assoc_column
            value = item_filter
        # filter via index (note that this is used via 0-based indexing
        # for use with the xpath of Item a 1 must be added to the index)
        elif isinstance(item_filter, int):
            start = item_filter + 1
            stop = start + 1
            key = "None"
            value = None
        # no filter
        elif item_filter is None:
            key = "None"
            value = None
        else:
            raise TypeError("item_filter must be of type: string, dict, int, or None!")

        for i in range(start, stop):
            item = self.item_class(self, index=i)
            if getattr(item, key, None) == value:
                yield item


class FlashMessage(ParametrizedView):
    """Represent a Patternfly Inline Notification:
    https://www.patternfly.org/v3/pattern-library/communication/inline-notifications/
    Parametrized by the XPath index of the notification within the containing FlashMessages block.
    """
    TYPE_MAPPING = {
        'alert-warning': 'warning',
        'alert-success': 'success',
        'alert-danger': 'error',
        'alert-info': 'info'
    }

    PARAMETERS = ('index',)
    ROOT = ParametrizedLocator('.//div[contains(@class, "alert") and position()={index}]')

    TEXT_LOCATOR = './strong'
    DISMISS_LOCATOR = './button[contains(@class, "close")]'
    ICON_LOCATOR = './span[contains(@class, "pficon")]'

    # XPath index starting at 1
    index = Parameter('index')

    @property
    def text(self):
        """Return the message text of the notification."""
        return self.browser.text(self.TEXT_LOCATOR, parent=self)

    def dismiss(self):
        """Close the notification."""
        self.logger.info(f"Dismissed notification with text {self.text!r}.")
        return self.browser.click(self.DISMISS_LOCATOR, parent=self)

    @property
    def icon(self):
        try:
            e = self.browser.element(self.ICON_LOCATOR, parent=self)
        except NoSuchElementException:
            return None

        for class_ in self.browser.classes(e):
            if class_.startswith('pficon-'):
                return class_[7:]
        else:
            return None

    @property
    def type(self):
        classes = self.browser.classes(self)
        for class_ in classes:
            if class_ in self.TYPE_MAPPING:
                return self.TYPE_MAPPING[class_]
        else:
            raise ValueError("Could not find a proper notification type."
                             f" Available classes: {self.TYPE_MAPPING!r}."
                             f" Notification types: {classes!r}.")


class FlashMessages(View):
    """Represent the div block containing the individual inline notifications."""
    ROOT = './/div[@id="flash_msg_div"]'
    MSG_LOCATOR = './div[contains(@class, "flash_text_div")]/div[contains(@class, "alert")]'
    msg_class = FlashMessage

    def __getitem__(self, msg_filter):
        """Allow the direct selection of a FlashMessage with a filter:
           msg = view.flash[msg_filter]
           msg_filter can be of type dict, int, or None.
        """
        if isinstance(msg_filter, int):
            return next(self.messages(index=msg_filter))
        elif isinstance(msg_filter, dict) or msg_filter is None:
            return self.messages(**msg_filter)
        else:
            raise ValueError(f"msg_filter {msg_filter} is of type {type(msg_filter)}"
                             " but must be dict, int, or None.")

    @property
    def msg_count(self):
        c = 0
        try:
            c = len(self.browser.elements(self.MSG_LOCATOR, parent=self))
        except NoSuchElementException:
            pass
        return c

    def messages(self, **msg_filter):
        """Return a generator for all notifications matching the msg_filter.
        The total number of notifications is re-checked each time, and the parametrized XPath
        index is re-calculated if necessary, in case any of the previously-yielded
        notifications have been dismissed.

        Kwargs:
               text: :py:class:`str` or :py:class:`Pattern` to match against the notification text.
                     Default: None.
                  t: :py:class:`str` or list/set/tuple of them, to match against the notification
                     type. Default: None.
            partial: if True, then a partial (sub-string) text match will be performed.
                     Default: False.
            inverse: if True, perform an inverse search.
                     Default: False.
              index: The (0-based) index of the notification in the list to return.
                     Default: None.
        """
        text = msg_filter.get('text', None)
        t = msg_filter.get('t', None)
        partial = msg_filter.get('partial', False)
        inverse = msg_filter.get('inverse', False)
        index = msg_filter.get('index', None)

        types = t if isinstance(t, (tuple, list, set, type(None))) else (t, )
        op = not_ if inverse else bool

        # Log message describing the type of notification lookup.
        if any((text, types, partial, inverse)):
            log_msgs = [
                f"pattern: {text.pattern!r}" if isinstance(text, Pattern) else f"text: {text!r}",
                f"type(s): {types!r}",
                f"partial: {partial}",
                f"inverse: {inverse}",
            ]
            log_msg = f"Performing match of notifications, {', '.join(log_msgs)}."
        elif isinstance(index, int):
            log_msg = f"Reading notification with index {index}."
        else:
            log_msg = "Reading all notifications."

        self.logger.info(log_msg)

        # Filter via index (starting from 0).
        # Add 1 for the XPath index.
        if isinstance(index, int):
            start = index + 1
            stop = start + 1
        else:
            start = 1
            stop = self.msg_count + 1

        for i in range(start, stop):
            if isinstance(index, int):
                j = i
            else:
                new_stop = self.msg_count + 1
                j = i - (stop - new_stop)

            msg = self.msg_class(self, index=j)

            if types and not op(msg.type in types):
                continue
            if isinstance(text, Pattern) and not op(text.match(msg.text)):
                continue
            if isinstance(text, str) and not op(
                    (partial and text in msg.text) or (not partial and text == msg.text)):
                continue

            yield msg

    @retry_element
    def read(self, **msg_filter):
        """Return a list containing the notifications' text."""
        return [msg.text for msg in self.messages(**msg_filter)]

    @retry_element
    def dismiss(self):
        """Dismiss all notifications."""
        for msg in self.messages():
            msg.dismiss()

    def assert_no_error(self, ignore_messages=None):
        """Assert no error messages present.

        Kwargs:
               ignore_messages: :py:class:`list` of notification text to ignore. Default: None
        """
        if ignore_messages is None:
            ignore_messages = []
        msg_filter = {"t": {"success", "info", "warning"}, "inverse": True}

        self.logger.info("Asserting there are no error notifications.")
        errs = self.read(**msg_filter)
        if set(errs) - set(ignore_messages):
            self.logger.error(errs)
            raise AssertionError(f"assert_no_error: found error notifications {errs}")

    def assert_message(self, text, t=None, partial=False):
        msg_filter = {'text': text, 't': t, 'partial': partial}
        all_msgs = self.read()
        if not self.read(**msg_filter):
            raise AssertionError(
                "assert_message: failed to find matching notifications."
                f" Available notifications: {all_msgs}"
            )

    def assert_success_message(self, text, t=None, partial=False):
        self.assert_no_error()
        self.assert_message(text, t=(t or 'success'), partial=partial)

    @property
    def is_displayed(self):
        return self.parent_browser.is_displayed(self.ROOT)
