import os
import sys
from datetime import datetime

import pkg_resources

__distribution = pkg_resources.get_distribution("widgetastic.patternfly")

# update sys.path so autodoc can import the modules
modules_path = os.path.abspath("../src/widgetastic_patternfly")
sys.path.insert(0, modules_path)

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

master_doc = "index"

# General information about the project.
project = __distribution.project_name
copyright = f"2016-{datetime.now().year}, Milan Falešník (Apache license 2)"
author = "Milan Falešník"


# The full version, including alpha/beta/rc tags.
release = __distribution.version
version = ".".join(release.split(".")[:2])

exclude_patterns = ["_build"]

html_theme = "default"

templates_path = ["_templates"]


def run_apidoc(_):
    from sphinx.ext.apidoc import main as apidoc_main

    cur_dir = os.path.abspath(".")
    output_path = os.path.join(cur_dir, "source")
    apidoc_main(["-e", "-f", "-o", output_path, modules_path, "--force"])


def setup(app):
    app.connect("builder-inited", run_apidoc)
