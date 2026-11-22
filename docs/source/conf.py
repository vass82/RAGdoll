from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.errors import ExtensionError

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGE_HTML_DIR = REPO_ROOT / "htmlcov"
GENERATED_OPENAPI_PATH = Path("_generated") / "openapi.json"

project = "RAGdoll"
copyright = "Peter Vass"
author = "Peter Vass"
release = "0.0.1"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",  # handy source links; disable if it starts throwing build/index errors again
    "autoapi.extension",
    "sphinxcontrib.openapi",
]

autoapi_dirs = ["../../app"]
autoapi_root = "python-api"
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


def _write_openapi_spec(app: Sphinx) -> None:
    """Export the live FastAPI OpenAPI schema for the HTTP API reference.

    :param app: The Sphinx application being initialised.
    :type app: Sphinx
    """
    sys.path.insert(0, str(REPO_ROOT))
    from app.main import app as ragdoll_api

    spec_path = Path(app.srcdir) / GENERATED_OPENAPI_PATH
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        json.dumps(ragdoll_api.openapi(), indent=2) + "\n", encoding="utf-8"
    )


def _require_coverage_report(app: Sphinx) -> None:
    """Fail the HTML build early if the coverage report has not been generated.

    :param app: The Sphinx application being initialised.
    :type app: Sphinx
    :raises ExtensionError: If ``htmlcov/index.html`` does not exist.
    """
    if app.builder.format != "html":
        return
    if not (COVERAGE_HTML_DIR / "index.html").is_file():
        raise ExtensionError(
            "Coverage report not found at htmlcov/. Run "
            "'bash scripts/build_docs.sh' or generate it with 'uv run pytest "
            "--cov=app --cov-report=html' before building the documentation."
        )


def _publish_coverage_report(app: Sphinx, exception: Exception | None) -> None:
    """Copy the coverage HTML report into the built site.

    :param app: The Sphinx application that finished building.
    :type app: Sphinx
    :param exception: The build exception, if the build failed.
    :type exception: Exception | None
    """
    if exception is not None or app.builder.format != "html":
        return
    target = Path(app.outdir) / "coverage_html"
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(COVERAGE_HTML_DIR, target)


def setup(app: Sphinx) -> None:
    """Register the build hooks for the OpenAPI spec and coverage report.

    :param app: The Sphinx application.
    :type app: Sphinx
    """
    app.connect("builder-inited", _write_openapi_spec)
    app.connect("builder-inited", _require_coverage_report)
    app.connect("build-finished", _publish_coverage_report)
