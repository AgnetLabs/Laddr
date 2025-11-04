# MkDocs documentation

This directory contains the MkDocs setup for comprehensive Laddr docs. All Markdown pages (`docs/`) are built into static HTML via `mkdocs build`.

## Install

```bash
pip install -r docs-requirements.txt
```

## Preview locally

```bash
mkdocs serve
# Open http://localhost:8000
```

## Build static site

```bash
mkdocs build
# Output in site/
```

## Structure

- `mkdocs.yml` – Configuration (theme, nav, plugins)
- `docs/` – Markdown pages:
  - `index.md` – Home
  - `getting-started.md`, `configuration.md` – Guides
  - `guides/recipes.md` – Code snippets and edge cases
  - `cli/commands.md` – Auto-rendered CLI help (mkdocs-click)
  - `api/routes.md` – HTTP API examples
  - `reference/` – Auto-rendered docstrings (mkdocstrings)
- `docs-requirements.txt` – Pinned deps for building docs

## Key plugins

- **mkdocs-material** – Theme
- **mkdocstrings[python]** – Render Python docstrings as reference
- **mkdocs-click** – Render Click CLI commands
- **mkdocs-autorefs** – Cross-referencing

## How it works

`mkdocstrings` reads your Python source via import. The `setup_commands` in `mkdocs.yml` adds `lib/laddr/src` to sys.path so the `laddr` package is importable during build.
