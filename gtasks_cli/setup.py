from setuptools import setup, find_packages
import os

# Read README.md
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A powerful CLI for managing Google Tasks"

# Read requirements.txt
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = fh.read().splitlines()
else:
    requirements = []

setup(
    name="gtasks-cli",
    version="0.1.4",
    author="Google Tasks CLI Team",
    author_email="example@example.com",
    description="A powerful command-line interface for managing Google Tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/gtasks-cli",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gtasks=gtasks_cli.main:main",
        ],
    },
    include_package_data=True,
)