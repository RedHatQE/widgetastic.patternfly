# -*- coding: utf-8 -*-
from wait_for import wait_for
from widgetastic.exceptions import NoSuchElementException, UnexpectedAlertPresentException
from widgetastic.widget import Widget, ClickableMixin
from widgetastic.utils import ParametrizedLocator
from widgetastic.xpath import quote

from .exceptions import DropdownDisabled, DropdownItemNotFound, DropdownItemDisabled


class Kebab(Widget):
    """Represents the Patternfly 'Kebab' widget which looks like 3 dots that open a dropdown.

    Args:
        button_id: id of the button inside ``div.dropdown-kebab-pf``.
    """
    ROOT = ParametrizedLocator(
        './/div[contains(@class, "dropdown-kebab-pf") and ./button[@id={@button_id|quote}]]')
    UL = './ul[contains(@class, "dropdown-menu")]'
    BUTTON = './button'
    ITEMS = './ul/li/a'
    ITEM = ITEMS + '[normalize-space(.)={}]'

    def __init__(self, parent, button_id, logger=None):
        super(Kebab, self).__init__(parent, logger=logger)
        self.button_id = button_id

    @property
    def is_opened(self):
        return self.browser.is_displayed(self.UL)

    @property
    def items(self):
        return [self.browser.text(item) for item in self.browser.elements(self.ITEMS)]

    def open(self):
        if not self.is_opened:
            self.browser.click(self.BUTTON)

    def close(self):
        if self.is_opened:
            self.browser.click(self.BUTTON)

    def select(self, item, close=True):
        try:
            self.open()
            self.browser.click(self.ITEM.format(quote(item)))
        finally:
            if close:
                self.close()


class NavDropdown(Widget, ClickableMixin):
    """The dropdowns used eg. in navigation. Usually located in the top navbar."""

    def __init__(self, parent, locator, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __locator__(self):
        return self.locator

    def read(self):
        return self.text

    @property
    def expandable(self):
        try:
            self.browser.element('./a/span[contains(@class, "caret")]', parent=self)
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
            return self.browser.text('./a/p', parent=self)
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
        return '{}({!r})'.format(type(self).__name__, self.locator)


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
                raise DropdownItemDisabled(
                    'Item "{}" of dropdown "{}" is disabled'.format(item, self.text))
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

    @property
    def currently_selected(self):
        """Returns the currently selected item text."""
        return self.browser.text(self.BUTTON_LOCATOR, parent=self)

    def item_select(self, item, *args, **kwargs):
        super(SelectorDropdown, self).item_select(item, *args, **kwargs)
        wait_for(lambda: self.currently_selected == item, num_sec=3, delay=0.2)

    def read(self):
        return self.currently_selected

    def fill(self, value):
        if value == self.currently_selected:
            return False
        self.item_select(value)
        return True

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.b_attr, self.b_attr_value)


__all__ = ['Kebab', 'NavDropdown', 'Dropdown', 'SelectorDropdown']
