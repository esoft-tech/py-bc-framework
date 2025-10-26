import sys
from pathlib import Path

sys.path.insert(0, str(Path("..", "src").resolve()))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "py-bc-configs"
copyright = "2025, Artem Shirokikh (job@artemetr.ru), Esoft (it@esoft.tech)"
author = "Artem Shirokikh (job@artemetr.ru), Esoft (it@esoft.tech)"
release = "0.3.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "myst_parser",
    "sphinx.ext.viewcode",
    "sphinx.ext.linkcode",
    "sphinxcontrib.autodoc_pydantic",
]

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# -- Additional options ------------------------------------------------------
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True


def linkcode_resolve(domain, info):
    return None
