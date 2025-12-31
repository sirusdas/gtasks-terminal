# PyPI Upload Guide for gtasks-cli

This document explains how to build and upload the `gtasks-cli` package to PyPI.

## Prerequisites

Before uploading to PyPI, you need:

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/)
2. **API Token**: Generate an API token from your PyPI account settings
3. **Required Tools**: Install the following Python packages:
   ```bash
   pip install --upgrade build twine
   ```

## Preparing for Upload

1. **Update Version**: Make sure to update the version number in both `pyproject.toml` and `setup.py`
2. **Update Changelog**: Ensure the changelog is up-to-date
3. **Test Installation**: Test the package locally:
   ```bash
   pip install dist/gtasks_cli-x.x.x.tar.gz
   ```

## Build and Upload Process

### Using Provided Scripts

We provide both shell and batch scripts for uploading:

#### On Linux/macOS:
```bash
./upload.sh
```

#### On Windows:
```cmd
upload.bat
```

### Manual Process

If you prefer to do it manually:

1. **Clean Previous Builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

2. **Build the Package**:
   ```bash
   python -m build
   ```

3. **Verify the Build**:
   ```bash
   python -m twine check dist/*
   ```

4. **Upload to Test PyPI (Optional but Recommended)**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

5. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

## Test PyPI First (Recommended)

Before uploading to the real PyPI, test with Test PyPI:

1. **Upload to Test PyPI**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. **Test Installation from Test PyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ gtasks-cli
   ```

## Important Notes

- Always increment the version number before uploading
- The `build` tool creates both source distribution (`.tar.gz`) and wheel (`.whl`) files
- Use `twine check` to validate your package before uploading
- Store your PyPI credentials securely
- Consider using Test PyPI first to validate your package

## Troubleshooting

### Common Issues:

1. **Version Already Exists**: Increment the version number in `pyproject.toml` and `setup.py`
2. **Build Fails**: Ensure all dependencies are properly specified
3. **Upload Fails**: Check your PyPI credentials and permissions

## Verification

After uploading, verify that:

1. The package page displays correctly on PyPI
2. Installation works: `pip install gtasks-cli`
3. The command works: `gtasks --help`
4. All functionality is available as expected