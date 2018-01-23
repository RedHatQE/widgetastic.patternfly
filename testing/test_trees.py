# -*- coding: utf-8 -*-
from widgetastic.widget import View
from widgetastic_patternfly import CheckableBootstrapTreeview


def test_tree_check(browser):
    class TestView(View):
        tree = CheckableBootstrapTreeview('test-tree')

    view = TestView(browser)
    # testing page should have [Parent 2, Child A] selected by default
    expected_paths = [
        ('Parent 1', 'Child 1'),
        ('Parent 1', 'Child 1', 'Grandchild 1'),
        ('Parent 1', 'Child 2'),
        ('Parent 2', 'Child A')
    ]
    for expected in expected_paths:
        contents = view.tree.read_contents(nodeid='0')
        assert view.tree.has_path(*expected)
    assert view.tree.node_checked('Parent 2', 'Child A')
