# Releasing 0.2.14

This patch release delivers the fixes merged in #30: reliable plugin initialization,
optional PXMeter/DockQ handling, and ESM3 API error reporting. It advances the
package version so installations on 0.2.13 can discover an update through the
startup loader. See #28 for the installation fix promised for the next PyPI release.

## Preflight

- Wait for regression and distribution jobs on the release PR to pass, then merge.
- Recheck https://pypi.org/pypi/pymolfold/json before publishing. At preparation
  time, the latest version was 0.2.13 and 0.2.14 was absent. If 0.2.14 has since
  been used, choose a fresh version; do not reuse published artifact filenames.
- A maintainer must confirm that the repository Actions secret `PYPI_API_TOKEN`
  exists, is valid, and grants upload access to the `pymolfold` PyPI project.
  Secret presence and PyPI account permissions were not verifiable through the
  repository connection. The current workflow uses token authentication rather
  than Trusted Publishing.

## Validate locally

Use Python 3.10 or newer in a clean checkout and virtual environment:

```sh
python -m pip install build twine pytest packaging requests httpx fastapi uvicorn python-dotenv
python -m pytest
python -m build
python -m twine check --strict dist/*
python scripts/check_release.py
```

Start with an empty `dist/` directory. The default build creates an sdist and
builds the wheel from that sdist. Validation checks version metadata, package
modules, GUI JSON data, the PyMOL plugin entry point, and optional metrics metadata
without importing PyMOL or downloading the full inference dependencies.

## Publish and verify

1. Create tag `v0.2.14` at the merged release commit and **publish a GitHub Release**
   for that tag. A merge, tag push, or draft release alone does not trigger the
   `Upload Python Package` workflow (`release: published`).
2. Watch that workflow finish successfully. It builds and validates distributions,
   then uploads both files to PyPI with `PYPI_API_TOKEN`.
3. Confirm https://pypi.org/project/pymolfold/0.2.14/ contains both the wheel and
   source archive and that the PyPI JSON endpoint reports latest version 0.2.14.
4. In a Python 3.10+ PyMOL environment with 0.2.13 installed, restart using the
   startup loader with network access and verify the upgrade to 0.2.14 and plugin
   initialization. Manual alternative using that environment's Python:
   `python -m pip install --upgrade pymolfold==0.2.14`.
5. Verify basic commands without the metrics extra; install `pymolfold[metrics]`
   only for optional metrics functionality. Full PyMOL/inference smoke testing is
   still required; artifact checks and offline tests do not exercise a real GUI,
   inference APIs, or every dependency/platform combination.

Suggested release notes: Fix plugin initialization and installation error
reporting; keep PXMeter/DockQ optional; handle ESM3 API errors. Existing 0.2.13
users can receive these fixes through the startup update check after PyPI publication.
