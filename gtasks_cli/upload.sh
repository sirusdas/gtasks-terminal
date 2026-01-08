#!/bin/bash
# Script to build and upload gtasks-cli to PyPI

set -e  # Exit on any error

echo "Starting PyPI upload process for gtasks-cli..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "setup.py" ]; then
    echo "Error: pyproject.toml or setup.py not found in current directory."
    echo "Please run this script from the gtasks_cli directory."
    exit 1
fi

# Check if required tools are installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH."
    exit 1
fi

# Install build tools if not already installed
echo "Installing/Updating build tools..."
pip install --upgrade build twine

# Clean previous builds if they exist
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true

# Build the package
echo "Building the package..."
python3 -m build

# Check if build was successful by looking for files in dist/
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "Build failed. Please check the error messages above."
    exit 1
fi

echo "Build completed successfully!"
echo "Built files:"
ls -la dist/

# Ask for confirmation before uploading
echo
read -p "Do you want to upload to PyPI? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Upload to PyPI
    echo "Uploading to PyPI..."
    python3 -m twine upload dist/*
    
    if [ $? -eq 0 ]; then
        echo "Successfully uploaded to PyPI!"
    else
        echo "Upload failed. Please check the error messages above."
        exit 1
    fi
else
    echo "Upload cancelled by user. Files are available in dist/ directory."
fi

echo "PyPI upload process completed."