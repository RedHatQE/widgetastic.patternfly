# module for patternfly utility classes and methods
from aenum import Constant


class IconConstants(Constant):
    """class to hold just the icon constants

    References:
        https://www.patternfly.org/styles/icons/
    """
    ADD = 'pficon-add-circle-o'
    APPLICATIONS = 'pficon-applications'
    ARROW = 'pficon-arrow'
    CLUSTER = 'pficon-cluster'
    CONTAINER_NODE = 'pficon-container-node'
    CPU = 'pficon-cpu'
    ERROR = 'pficon-error-circle-o'
    HOME = 'pficon-home'
    OK = 'pficon-ok'
    WARNING = 'pficon-warning-triangle-o'
    REFRESH = 'fa-refresh'

    @classmethod
    def icon_strings(cls):
        return {a: s for a, s in vars(IconConstants).items() if isinstance(s, Constant)}


class PFIcon(object):
    """Class to enumerate the patternfly default icons

    pficon-* markup classes have a variety of strings, this class should serve to prevent widget
    classes from having to parse, pass, or depend on string fragments
    """

    icons = IconConstants

    @classmethod
    def icon_from_element(cls, element, browser):
        """Taking a webelement, scan its child element classes for pficon and fa, return icon state

        Args:
            element: webelement object that will be searched for pficon classes
            browser: browser instance to query child elements and classes

        Raises:
            widgetastic.exceptions.NoSuchElementException when no icon span found
        """

        els = browser.elements(
            './/*[contains(@class, "pficon") or contains(@class, "fa")]',
            parent=element
        )
        if len(els) != 1:
            return None  # multiple icons

        icon_class = [c
                      for c in browser.classes(els.pop())
                      if c.startswith('pficon-') or c.startswith('fa-')]
        # slice off first 6 chars if a class was found
        icon_name = icon_class.pop() if icon_class else None
        icons = [
            getattr(cls.icons, attr, None)
            for attr, icon_string in cls.icons.icon_strings().items()
            if icon_string == icon_name
        ]
        return icons.pop() if icons else None
