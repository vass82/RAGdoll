.. _coverage_report:

Code coverage
=============

This page explains the code coverage measurement for the ``app`` package and
links to the full HTML report.

Open the full report: `HTML coverage report <coverage_html/index.html>`_.

What coverage measures
----------------------

Code coverage records which lines of the application were executed while the
test suite ran. This documentation uses **statement coverage**, measured by
`coverage.py <https://coverage.readthedocs.io/>`_ through the
`pytest-cov <https://pytest-cov.readthedocs.io/>`_ plugin.

For each module, the report gives:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Meaning
   * - ``Stmts``
     - The number of executable statements in the module.
   * - ``Miss``
     - The number of statements that no test executed.
   * - ``Cover``
     - ``(Stmts - Miss) / Stmts``, shown as a percentage.
   * - ``Missing``
     - The line numbers that were not executed (only in the terminal and HTML
       reports).

The HTML report marks each line as executed, not executed, or excluded.

Interpreting the percentage
---------------------------

A high percentage means that most statements were run at least once. A low
percentage means that large parts of the code are never exercised by the
tests. It does not show that the tests check the results. A test that calls a
function and asserts nothing still counts as coverage.

Use the missing line numbers as a guide. Read the uncovered lines to decide
whether they need a test, or whether they are defensive code that cannot be
reached through the public interface.

What the current report covers
------------------------------

The report was produced from the full test suite (``tests/``), with coverage
measured only for ``app/``. The result is a snapshot from the most recent run
of the command in :ref:`coverage_report_generation`. The HTML report linked
above is the authoritative result for each build.

.. list-table:: Snapshot from the test run that produced this page
   :header-rows: 1
   :widths: 40 20 20 20

   * - Measure
     - Value
     - Statements
     - Missed
   * - All of ``app/``
     - 99%
     - 293
     - 2

The suite ran 78 tests, all of which passed. Every module in ``app/`` is at
100% except the two below.

.. list-table:: Modules below 100%
   :header-rows: 1
   :widths: 40 20 40

   * - Module
     - Missing line
     - Reason
   * - ``app/infrastructure/document_loader.py``
     - 46
     - The ``continue`` branch for a path that matches ``*.md`` but is not a
       regular file, such as a directory with that name.
   * - ``app/infrastructure/llm.py``
     - 24
     - The ``ValueError`` for an unsupported provider. The ``LLM_PROVIDER``
       setting only accepts ``openai`` and ``ollama``, so this line is a
       defensive guard that is not reachable through configuration.

.. _coverage_report_generation:

How the report is generated
---------------------------

The coverage reports are produced by the same command that builds this
documentation:

.. code-block:: bash

   bash scripts/build_docs.sh

The script runs the test suite with coverage and then builds the Sphinx site.
The equivalent test command, run from the repository root, is:

.. code-block:: bash

   uv run --locked pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-report=html

It writes three outputs:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Output
     - Location
     - Purpose
   * - Terminal summary
     - Standard output
     - A quick check after running the tests.
   * - XML report
     - ``coverage.xml``
     - A machine-readable file for CI tools and coverage services.
   * - HTML report
     - ``htmlcov/index.html``
     - A browsable report with line-by-line highlighting.

The generated ``htmlcov/`` directory and ``coverage.xml`` are listed in
``.gitignore`` and are not committed. When the HTML documentation is built,
the Sphinx configuration copies ``htmlcov/`` into the site as
``coverage_html/``, so the link above works in the published documentation. If
the report is missing, the HTML build stops with an error that explains which
command to run.

Limitations
-----------

Coverage is a useful signal, but it has limits:

* It measures execution, not correctness. A line can run and still produce the
  wrong result.
* It does not measure branch combinations, input values, or concurrency.
  ``--cov-branch`` adds branch coverage, which this project does not enable.
* A high number can hide weak tests. Tests that exercise code without
  asserting its behaviour raise the percentage without protecting the code.
* A low number in one module is not always a problem. Some lines are defensive
  code that is hard to reach, and forcing a test for every such line can add
  noise.
* It measures only ``app/``. Tests, scripts, and configuration files are not
  part of the percentage. Modules in ``app/`` that no test imports still appear
  in the report, with 0% coverage.

Treat coverage as one input to a review. Combine it with the test assertions,
code review, and the behaviour described in :ref:`http_api`.
