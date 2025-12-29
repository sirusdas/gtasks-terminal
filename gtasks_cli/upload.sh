#!/bin/bash
# Upload script for gtasks-cli to PyPI

set -e  # Exit on any error

echo "==========================================="
echo "Google Tasks CLI - PyPI Upload Script"
echo "==========================================="

# Check if build tools are installed
if ! command -v python -m build &> /dev/null; then
    echo "Installing build tools..."
    pip install build twine
fi

echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

echo "Building package..."
python -m build

echo "Checking package..."
twine check dist/*

echo "Package built successfully!"
echo "Files created:"
ls -la dist/

echo ""
echo "Choose upload target:"
echo "1) Upload to TestPyPI"
echo "2) Upload to PyPI (Production)"
read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    echo "Upload to TestPyPI complete!"
    echo ""
    echo "To test install from TestPyPI, run:"
    echo "pip install --index-url https://test.pypi.org/simple/ gtasks-cli"
elif [ "$choice" = "2" ]; then
    echo "Uploading to PyPI..."
    twine upload dist/*
    echo "Upload to PyPI complete!"
    echo ""
    echo "Package is now available at: https://pypi.org/project/gtasks-cli/"
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo ""
echo "Upload process completed!"