# How to Upload to PyPI

This document explains how to upload the Google Tasks CLI package to PyPI (Python Package Index).

**Note: The package is already published to PyPI and can be installed with `pip install gtasks-cli`. This document is maintained for reference and future updates.**

The latest version can be found at: https://pypi.org/project/gtasks-cli/

## Prerequisites

1. Make sure you have the latest versions of `build` and `twine` installed:
   ```
   pip install --upgrade build twine
   ```

2. You need a PyPI account. If you don't have one, register at https://pypi.org/account/register/

3. For testing purposes, you can use TestPyPI: https://test.pypi.org/account/register/

## Version Management

Before building and uploading a new version, you need to update the version number in two places:

1. [pyproject.toml](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/pyproject.toml) - Update the `version` field in the `[project]` section
2. [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py) - Update the `__version__` variable

We follow semantic versioning (SemVer) for version numbers: `MAJOR.MINOR.PATCH`

- MAJOR version when you make incompatible API changes
- MINOR version when you add functionality in a backward compatible manner
- PATCH version when you make backward compatible bug fixes

PyPI does not allow overwriting existing versions, so you must increment the version number for each new release.

## Building the Package

The package now uses `hatchling` as the build backend. Make sure it's installed:

```
pip install hatchling
```

To build the package:

```
cd gtasks_cli
python -m build
```

This will create a `dist/` directory with two files:
- A source distribution (`.tar.gz`)
- A built distribution (`.whl`)

## Uploading to TestPyPI (Recommended for testing)

1. Create an API token at https://test.pypi.org/manage/account/#api-tokens

2. Upload the package to TestPyPI:
   ```
   python -m twine upload --repository testpypi dist/*
   ```
   
   Twine will ask for a username and password. For the username, enter `__token__`. For the password, enter your API token.

3. Test the installation:
   ```
   pip install --index-url https://test.pypi.org/simple/ gtasks-cli
   ```

## Uploading to PyPI

1. Create an API token at https://pypi.org/manage/account/#api-tokens

2. Upload the package to PyPI:
   ```
   python -m twine upload dist/*
   ```
   
   Twine will ask for a username and password. For the username, enter `__token__`. For the password, enter your API token.

3. Your package will be available at https://pypi.org/project/gtasks-cli/

## Post-upload Verification

After uploading, you can verify the package installation with:
```
pip install gtasks-cli
gtasks --help
```

## Updating the Package

To release a new version:

1. Update the version in:
   - [pyproject.toml](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/pyproject.toml)
   - [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py)

2. Rebuild the package:
   ```
   python -m build
   ```

3. Upload the new version:
   ```
   python -m twine upload dist/*
   ```

## Troubleshooting

### License Metadata Issues

If you encounter metadata errors related to license fields during upload, make sure:
1. You're using `hatchling` as the build backend
2. The `license` field in `pyproject.toml` uses a valid SPDX identifier (e.g., "MIT")
3. The `[tool.hatch.build.targets.wheel]` section properly configures the packages to include

### Build Backend Issues

If you experience issues with the build process:
1. Ensure `hatchling` is properly installed
2. Verify that the `[tool.hatch.build.targets.wheel]` section in `pyproject.toml` contains the correct package paths
3. Check that your package directory structure matches the configuration

### File Already Exists Error

If you get an error like `File already exists`, it means you're trying to upload a version that already exists on PyPI. PyPI does not allow overwriting existing versions for security and integrity reasons. You must increment the version number in both [pyproject.toml](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/pyproject.toml) and [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py), then rebuild and re-upload.