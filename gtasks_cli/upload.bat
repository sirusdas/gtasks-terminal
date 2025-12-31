@echo off
REM Script to build and upload gtasks-cli to PyPI

echo Starting PyPI upload process for gtasks-cli...

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo Error: pyproject.toml not found in current directory.
    echo Please run this script from the gtasks_cli directory.
    exit /b 1
)

if not exist "setup.py" (
    echo Error: setup.py not found in current directory.
    echo Please run this script from the gtasks_cli directory.
    exit /b 1
)

REM Check if required tools are installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: python is not installed or not in PATH.
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed or not in PATH.
    exit /b 1
)

REM Install build tools if not already installed
echo Installing/Updating build tools...
pip install --upgrade build twine

REM Clean previous builds if they exist
echo Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"

REM Build the package
echo Building the package...
python -m build

REM Check if build was successful
if not exist dist (
    echo Build failed. Please check the error messages above.
    exit /b 1
)

echo Build completed successfully!
echo Built files:
dir dist

REM Ask for confirmation before uploading
echo.
set /p CONFIRM="Do you want to upload to PyPI? (y/N): "
if /I "%CONFIRM%"=="y" (
    REM Upload to PyPI
    echo Uploading to PyPI...
    python -m twine upload dist\*
    
    if errorlevel 1 (
        echo Upload failed. Please check the error messages above.
        exit /b 1
    ) else (
        echo Successfully uploaded to PyPI!
    )
) else (
    echo Upload cancelled by user. Files are available in dist/ directory.
)

echo PyPI upload process completed.