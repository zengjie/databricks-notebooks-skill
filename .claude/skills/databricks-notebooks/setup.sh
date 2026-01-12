#!/bin/bash
# Databricks Notebooks Skill - One-click Setup Script

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "=== Databricks Notebooks Skill Setup ==="
echo ""

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SKILL_DIR/scripts/requirements.txt" -q
echo "Dependencies installed."

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo ""
    echo "Creating .env from template..."
    cp "$SKILL_DIR/.env.example" "$PROJECT_ROOT/.env"
    echo "Please edit $PROJECT_ROOT/.env with your Databricks credentials."
    echo ""
    echo "Or run interactive setup:"
    echo "  $VENV_DIR/bin/python3 $SKILL_DIR/scripts/config_helper.py setup"
else
    echo ""
    echo "Testing Databricks connection..."
    if "$VENV_DIR/bin/python3" "$SKILL_DIR/scripts/config_helper.py" test 2>/dev/null; then
        echo ""
    else
        echo ""
        echo "Connection test failed. Please check your credentials in $PROJECT_ROOT/.env"
        echo "Or run: $VENV_DIR/bin/python3 $SKILL_DIR/scripts/config_helper.py setup"
    fi
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Usage examples:"
echo "  # List notebooks"
echo "  $VENV_DIR/bin/python3 $SKILL_DIR/scripts/databricks_client.py list \"/Users/you@example.com/\""
echo ""
echo "  # Export notebook"
echo "  $VENV_DIR/bin/python3 $SKILL_DIR/scripts/databricks_client.py export \"/Users/you@example.com/notebook\""
echo ""
echo "Tip: Add this alias to your shell profile:"
echo "  alias dbcli='$VENV_DIR/bin/python3 $SKILL_DIR/scripts/databricks_client.py'"
