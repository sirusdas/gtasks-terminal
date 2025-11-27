# How to Upload to PyPI

This document explains how to upload the Google Tasks CLI package to PyPI (Python Package Index).

**Note: The package is already published to PyPI and can be installed with `pip install gtasks-cli`. This document is maintained for reference and future updates.**

## Prerequisites

1. Make sure you have the latest versions of `build` and `twine` installed:
   ```
   pip install --upgrade build twine
   ```

2. You need a PyPI account. If you don't have one, register at https://pypi.org/account/register/

3. For testing purposes, you can use TestPyPI: https://test.pypi.org/account/register/

## Building the Package

The package configuration is ready and you can build it with:

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
   - [setup.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/setup.py)

2. Rebuild the package:
   ```
   python -m build
   ```

3. Upload the new version:
   ```
   python -m twine upload dist/*
   ```