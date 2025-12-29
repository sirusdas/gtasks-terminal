# PyPI Upload Guide for Google Tasks CLI

This document provides detailed instructions for uploading the Google Tasks CLI package to PyPI.

## Prerequisites

Before uploading to PyPI, you need:

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/)
2. **API Token**: Generate an API token from your PyPI account settings
3. **Python Build Tools**: Install required build tools
   ```bash
   pip install build twine
   ```

## Preparing Your Package

### 1. Verify Package Configuration

Make sure your package is properly configured:

- [pyproject.toml](pyproject.toml) has correct metadata
- [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py) has correct version
- [MANIFEST.in](MANIFEST.in) includes all necessary files
- [LICENSE](LICENSE) file exists
- [README.md](README.md) is up to date

### 2. Update Version Number

Make sure the version number is correct in both:
- [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py)
- [setup.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/setup.py) (if using)

### 3. Clean Previous Builds

Remove any previous build artifacts:

```bash
rm -rf dist/ build/ *.egg-info/
```

## Building the Package

### 1. Build the Distribution

```bash
python -m build
```

This creates:
- `dist/gtasks_cli-<version>.tar.gz` (source distribution)
- `dist/gtasks_cli-<version>-py3-none-any.whl` (wheel distribution)

### 2. Verify the Build

```bash
twine check dist/*
```

## Uploading to PyPI

### 1. Upload to TestPyPI (Optional but Recommended)

First test your upload on TestPyPI:

```bash
twine upload --repository testpypi dist/*
```

To install from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ gtasks-cli
```

### 2. Upload to PyPI

```bash
twine upload dist/*
```

You'll be prompted for your username and password, or you can use an API token.

## Using API Token (Recommended)

For better security, use an API token instead of username/password:

### 1. Create .pypirc file

Create `~/.pypirc` file with your credentials:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-api-token-here
```

### 2. Upload using the configuration

```bash
twine upload dist/*
```

## Automated Upload Script

You can create an upload script to automate the process:

```bash
#!/bin/bash
# upload.sh

set -e  # Exit on any error

echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

echo "Building package..."
python -m build

echo "Checking package..."
twine check dist/*

echo "Uploading to PyPI..."
twine upload dist/*

echo "Upload complete!"
```

Make it executable:

```bash
chmod +x upload.sh
```

## Version Management

### Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Incompatible API changes
- MINOR: Backward-compatible functionality
- PATCH: Backward-compatible bug fixes

### Bumping Version

1. Update version in [src/gtasks_cli/__init__.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/__init__.py)
2. Update version in [setup.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/setup.py) (if using)
3. Commit the changes
4. Create a git tag:
   ```bash
   git tag -a v0.1.3 -m "Release version 0.1.3"
   git push origin v0.1.3
   ```

## Troubleshooting

### Common Issues

1. **Missing Files in Distribution**
   - Check [MANIFEST.in](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/MANIFEST.in) includes all necessary files
   - Verify [pyproject.toml](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/pyproject.toml) includes all packages

2. **Metadata Issues**
   - Check for malformed metadata in [pyproject.toml](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/pyproject.toml)
   - Ensure license information is correctly specified

3. **Permission Issues**
   - Use API tokens instead of passwords
   - Verify your account has upload permissions for the package name

4. **Build Failures**
   - Ensure all dependencies are properly specified
   - Check that all imports work correctly

### Verification Steps

After upload, verify the package:

1. Visit the PyPI page for your package
2. Check that metadata is displayed correctly
3. Verify the README is rendered properly
4. Test installation in a fresh environment:
   ```bash
   python -m venv test_env
   source test_env/bin/activate  # On Windows: test_env\Scripts\activate
   pip install gtasks-cli
   gtasks --help
   ```

## Post-Upload Steps

1. **Update Documentation**: Update installation instructions in README
2. **Tag Release**: Create a git tag for the released version
3. **Announce Release**: If appropriate, announce the release on relevant channels
4. **Monitor**: Check for any issues reported by early adopters

## Automation with GitHub Actions (Optional)

For continuous deployment, you can set up GitHub Actions to automatically build and upload your package when you create a new release:

```yaml
name: Publish Python Package

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Remember to add your PyPI API token as a secret in your GitHub repository settings.

## Security Best Practices

- Always use API tokens instead of passwords
- Keep your API tokens secure and never commit them to version control
- Regularly rotate your API tokens
- Monitor your PyPI account for unauthorized access