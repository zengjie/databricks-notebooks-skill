# Databricks Notebooks Skill for Claude Code

A Claude Code skill that enables reading and editing Databricks notebooks directly from the CLI, with access to Unity Catalog schemas for intelligent code generation.

## Features

- List, export, import, and delete Databricks notebooks
- Cell-level editing support
- Unity Catalog schema browsing for code generation
- Automatic import verification

## Quick Start

```bash
# One-click setup
bash .claude/skills/databricks-notebooks/setup.sh

# Or manual setup
python3 -m venv .venv
.venv/bin/pip install -r .claude/skills/databricks-notebooks/scripts/requirements.txt
```

## Configuration

Create a `.env` file at project root:

```bash
cp .claude/skills/databricks-notebooks/.env.example .env
# Edit .env with your Databricks credentials
```

Or run interactive setup:

```bash
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/config_helper.py setup
```

## Usage

```bash
# List notebooks
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py list "/Users/you@example.com/"

# Export notebook
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py export "/Users/you@example.com/notebook"

# Import notebook (with verification)
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py import "/Users/you@example.com/notebook" \
    -f content.py -l PYTHON

# Browse catalog schemas
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py tables main default
```

## Documentation

See [SKILL.md](.claude/skills/databricks-notebooks/SKILL.md) for full documentation.

## License

MIT
