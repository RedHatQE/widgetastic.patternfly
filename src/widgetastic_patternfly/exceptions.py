# -*- coding: utf-8 -*-
import six


class CandidateNotFound(Exception):
    """
    Raised if there is no candidate found whilst trying to traverse a tree.
    """
    def __init__(self, d):
        self.d = d

    @property
    def message(self):
        return ", ".join("{}: {}".format(k, v) for k, v in six.iteritems(self.d))

    def __str__(self):
        return self.message


class DropdownDisabled(Exception):
    pass


class DropdownItemDisabled(Exception):
    pass


class DropdownItemNotFound(Exception):
    pass
