import os
from datetime import datetime

import pkg_resources

__distribution = pkg_resources.get_distribution("widgetastic.patternfly")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("http://docs.python.org/2.7", None),
    "pytest": ("http://pytest.org/latest/", None),
    "selenium": ("http://selenium-python.readthedocs.org/", None),
    "widgetastic.core": ("http://widgetasticcore.readthedocs.io/en/latest/", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

# General information about the project.
project = __distribution.project_name
copyright = f"2016-{datetime.now().year}, Milan Falešník (Apache license 2)"
author = "Milan Falešník"


# The full version, including alpha/beta/rc tags.
release = __distribution.version
version = ".".join(release.split(".")[:2])

exclude_patterns = []

pygments_style = "sphinx"
todo_include_todos = False


html_theme = "haiku"
html_static_path = ["_static"]

htmlhelp_basename = "deprecatedoc"


def run_apidoc(_):
    from sphinx.apidoc import main as apidoc_main

    modules = ["src/widgetastic_patternfly"]
    for module in modules:
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        output_path = os.path.join(cur_dir, module, "doc")
        apidoc_main(["-e", "-f", "-o", output_path, ".", "--force"])


def setup(app):
    app.connect("builder-inited", run_apidoc)
