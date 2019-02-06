from widgetastic.widget import View
from widgetastic_patternfly import BootstrapTreeview


def test_bootstrap_tree(browser):
    class TestView(View):
        tree = BootstrapTreeview(tree_id="treeview1")

    view = TestView(browser)

    # assert that tree is visible
    assert view.tree.is_displayed
    # assert that we have multiple roots in this tree view
    assert view.tree.root_item_count > 1
    # assert that we have multiple root items
    assert len(view.tree.root_items) > 1
    # TODO: add more to the widget in testing page so that we can test more complex
    #       functionality, such as currently_selected
