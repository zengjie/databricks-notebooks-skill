# Databricks Notebooks Skill for Claude Code

English | [中文](README_zh.md)

A [Claude Code](https://claude.ai/claude-code) skill that enables reading and editing Databricks notebooks directly from the CLI, with access to Unity Catalog schemas for intelligent code generation.

## Features

- List, export, import, and delete Databricks notebooks
- Cell-level editing support
- Unity Catalog schema browsing for code generation
- Automatic import verification to detect failed saves

## Installation

### 1. Copy the skill to your project

Copy the `.claude/skills/databricks-notebooks` directory to your project:

```bash
# Clone this repo
git clone https://github.com/zengjie/databricks-notebooks-skill.git

# Copy skill to your project
cp -r databricks-notebooks-skill/.claude/skills/databricks-notebooks YOUR_PROJECT/.claude/skills/
```

Or add as a git submodule:

```bash
git submodule add https://github.com/zengjie/databricks-notebooks-skill.git .claude/skills/databricks-notebooks-skill
```

### 2. Run setup

```bash
bash .claude/skills/databricks-notebooks/setup.sh
```

This will:
- Create a virtual environment at `.venv/`
- Install dependencies (databricks-sdk, python-dotenv)
- Create `.env` from template
- Test the connection

### 3. Configure Databricks credentials

Edit `.env` file at your project root:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

Or run interactive setup:

```bash
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/config_helper.py setup
```

## Usage with Claude Code

Once installed, the skill is automatically available in Claude Code. Simply ask Claude to:

- **"List my Databricks notebooks"**
- **"Edit the Playground notebook"**
- **"Create a new notebook called analytics"**
- **"Show me the schema for table main.sales.customers"**
- **"Add a SQL cell to query the users table"**

### Example Conversation

```
You: Edit my Playground notebook in Databricks

Claude: Let me export the Playground notebook...
[exports notebook, shows content]

You: Add a cell to query the latest 10 records from the users table

Claude: [Gets table schema, adds new SQL cell, imports back with verification]
Done! Added a new cell with the query.
```

## Manual CLI Usage

You can also use the scripts directly:

```bash
# List notebooks
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py list "/Users/you@example.com/"

# Export notebook
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py export "/Users/you@example.com/notebook"

# Import notebook (with automatic verification)
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py import "/Users/you@example.com/notebook" \
    -f content.py -l PYTHON

# Browse Unity Catalog
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py schemas prod
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py tables prod myschema
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py table-schema prod.myschema.mytable
```

## Project Structure

```
.claude/skills/databricks-notebooks/
├── SKILL.md                 # Skill definition and full documentation
├── .env.example             # Configuration template
├── setup.sh                 # One-click installation script
└── scripts/
    ├── databricks_client.py # Notebook CRUD operations
    ├── catalog_client.py    # Unity Catalog schema browsing
    ├── config_helper.py     # Databricks configuration management
    ├── notebook_parser.py   # Cell-level editing utilities
    └── requirements.txt     # Python dependencies
```

## Documentation

See [SKILL.md](.claude/skills/databricks-notebooks/SKILL.md) for complete documentation including:

- All available commands
- Notebook SOURCE format reference
- Cell-level editing workflows
- Unity Catalog browsing
- Troubleshooting guide

## License

MIT
