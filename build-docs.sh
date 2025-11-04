#!/bin/bash
# filepath: build-docs.sh

# Install dependencies
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python mkdocs-autorefs mkdocs-click

# Build static site
mkdocs build

# Output is in ./site/