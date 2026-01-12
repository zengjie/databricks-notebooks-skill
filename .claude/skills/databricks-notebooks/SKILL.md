---
name: databricks-notebooks
description: Edit Databricks notebooks and browse database schemas. Use when user wants to read, modify, create notebooks, or access table schemas for code generation.
allowed-tools: Read, Bash(python:*), Edit, Write
user-invocable: true
---

# Databricks Notebook Editor

This skill enables reading and editing Databricks notebooks directly from Claude Code, with access to Unity Catalog schemas for intelligent code generation.

## Quick Setup (Recommended)

Run the one-click setup script:

```bash
bash .claude/skills/databricks-notebooks/setup.sh
```

This will:
- Create a virtual environment at `.venv/`
- Install all dependencies
- Create `.env` from template (if not exists)
- Test the connection

## Manual Setup

### 1. Create Virtual Environment & Install Dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r .claude/skills/databricks-notebooks/scripts/requirements.txt
```

### 2. Configure Databricks (Interactive)

```bash
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/config_helper.py setup
```

### 3. Test Connection

```bash
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/config_helper.py test
```

## Configuration Management

Use `config_helper.py` to manage your Databricks configuration:

```bash
# Check current configuration status
.venv/bin/python3 scripts/config_helper.py check

# Interactive setup wizard
.venv/bin/python3 scripts/config_helper.py setup

# Set individual values
.venv/bin/python3 scripts/config_helper.py set-host https://your-workspace.cloud.databricks.com
.venv/bin/python3 scripts/config_helper.py set-token dapi...

# Test connection
.venv/bin/python3 scripts/config_helper.py test
```

Configuration is stored in `.env` file at project root:
```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

### Alternative: Manual Configuration

You can also set environment variables directly:
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

Or create `~/.databrickscfg`:
```ini
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = dapi...
```

## Available Commands

**Important**: Always use `.venv/bin/python3` to ensure correct environment.

### List Workspace Contents

```bash
.venv/bin/python3 scripts/databricks_client.py list "/Users/user@example.com/"
```

### Read/Export Notebook

```bash
.venv/bin/python3 scripts/databricks_client.py export "/Users/user@example.com/my-notebook"
```

### Get Notebook Status

```bash
.venv/bin/python3 scripts/databricks_client.py status "/Users/user@example.com/my-notebook"
```

### Save/Import Notebook

```bash
.venv/bin/python3 scripts/databricks_client.py import "/Users/user@example.com/my-notebook" \
    --content-file /tmp/notebook.py \
    --language PYTHON
```

**Note**: The import command will verify the content was saved correctly and show a diff if there's a mismatch.

### Delete Notebook

```bash
.venv/bin/python3 scripts/databricks_client.py delete "/Users/user@example.com/my-notebook"
```

## Notebook SOURCE Format

Databricks notebooks use SOURCE format with these conventions:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Title

# COMMAND ----------

def my_function():
    return "Hello"

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM table
```

- `# COMMAND ----------` separates cells
- `# MAGIC %<lang>` switches cell language (md, sql, python, scala, r)
- `# MAGIC` prefix for non-default language content

## Cell-Level Editing

Use `notebook_parser.py` for cell operations:

```bash
# Parse notebook into cells
.venv/bin/python3 scripts/notebook_parser.py parse < notebook.py

# Get specific cell
.venv/bin/python3 scripts/notebook_parser.py get-cell 2 < notebook.py

# Update specific cell
.venv/bin/python3 scripts/notebook_parser.py update-cell 2 --content "new code" < notebook.py

# Insert new cell
.venv/bin/python3 scripts/notebook_parser.py insert-cell 1 --content "# new cell" < notebook.py

# Delete cell
.venv/bin/python3 scripts/notebook_parser.py delete-cell 3 < notebook.py
```

## Workflows

### Read and Edit a Notebook

1. Export notebook to a local file:
   ```bash
   .venv/bin/python3 scripts/databricks_client.py export /path/to/notebook > /tmp/notebook.py
   ```

2. Edit the content in `/tmp/notebook.py` using Write tool or editor

3. Import back (with automatic verification):
   ```bash
   .venv/bin/python3 scripts/databricks_client.py import /path/to/notebook \
       --content-file /tmp/notebook.py --language PYTHON
   ```

### Create a New Notebook

1. Create content file with Databricks format using Write tool
2. Import:
   ```bash
   .venv/bin/python3 scripts/databricks_client.py import /path/to/new-notebook \
       --content-file content.py --language PYTHON
   ```

### Edit a Specific Cell

1. Export notebook to temp file
2. Use `notebook_parser.py update-cell` to modify the cell
3. Import the modified notebook back

## Supported Languages

- PYTHON
- SQL
- SCALA
- R

## Schema Browsing (Unity Catalog)

Use `catalog_client.py` to browse database schemas for code generation:

### List Catalogs

```bash
.venv/bin/python3 scripts/catalog_client.py catalogs
```

### List Schemas in a Catalog

```bash
.venv/bin/python3 scripts/catalog_client.py schemas main
```

### List Tables in a Schema

```bash
.venv/bin/python3 scripts/catalog_client.py tables main default
```

### Get Table Schema (for code generation)

```bash
.venv/bin/python3 scripts/catalog_client.py table-schema main.default.customers
```

Returns JSON with column names, types, and comments.

### Generate DDL

```bash
.venv/bin/python3 scripts/catalog_client.py ddl main.default.customers
```

### Search Tables

```bash
.venv/bin/python3 scripts/catalog_client.py search main customer
```

## Code Generation Workflow

When generating SQL or PySpark code that references tables:

1. Get the table schema:
   ```bash
   .venv/bin/python3 scripts/catalog_client.py table-schema main.sales.customers
   ```

2. Use the column information to generate accurate code:
   - Correct column names
   - Appropriate data types
   - Proper NULL handling

Example output:
```json
{
  "name": "customers",
  "full_name": "main.sales.customers",
  "columns": [
    {"name": "customer_id", "type": "BIGINT", "nullable": false},
    {"name": "name", "type": "STRING", "nullable": true},
    {"name": "created_at", "type": "TIMESTAMP", "nullable": false}
  ]
}
```

## Troubleshooting

### "command not found: python"

Use `python3` instead of `python`, or use the full venv path:
```bash
.venv/bin/python3 scripts/databricks_client.py ...
```

### "externally-managed-environment" error

Create a virtual environment first:
```bash
python3 -m venv .venv
.venv/bin/pip install -r .claude/skills/databricks-notebooks/scripts/requirements.txt
```

### Import succeeds but content not updated

- Ensure you're using `.venv/bin/python3` (not system python)
- Create content files using Write tool instead of heredoc
- The improved import command now verifies content after saving
