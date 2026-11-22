from __future__ import annotations

project = "RAGdoll"
copyright = "Peter Vass"
author = "Peter Vass"
release = "0.0.1"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",  # handy source links; disable if it starts throwing build/index errors again
    "autoapi.extension",
]

autoapi_dirs = ["../../app"]
autoapi_root = "src-api"
autoapi_member_order = "bysource"
autoapi_python_class_content = "both"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

suppress_warnings = [
    "autoapi.python_import_resolution",
]

autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 1

templates_path = ["_templates"]
exclude_patterns = ["_build", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_sidebars = {
    "index": ["sidebarintro.html", "sourcelink.html", "searchbox.html", "hacks.html"],
    "**": [
        "sidebarlogo.html",
        "localtoc.html",
        "relations.html",
        "sourcelink.html",
        "searchbox.html",
        "hacks.html",
    ],
}
