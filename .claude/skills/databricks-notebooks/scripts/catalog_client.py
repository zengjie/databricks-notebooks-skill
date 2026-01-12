#!/usr/bin/env python3
"""Unity Catalog operations for schema access and code generation.

This script provides CLI commands for browsing Databricks Unity Catalog
to support intelligent code generation in notebooks.

Usage:
    python catalog_client.py catalogs
    python catalog_client.py schemas <catalog>
    python catalog_client.py tables <catalog> <schema>
    python catalog_client.py table-schema <catalog.schema.table>

Environment:
    DATABRICKS_HOST: Workspace URL (e.g., https://xxx.cloud.databricks.com)
    DATABRICKS_TOKEN: Personal access token
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Load .env file from project root or skill directory
try:
    from dotenv import load_dotenv
    # Try project root first, then skill directory
    for env_path in [Path.cwd() / ".env", Path(__file__).parent.parent / ".env"]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # python-dotenv not installed, rely on environment variables

try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    print("Error: databricks-sdk not installed. Run: pip install databricks-sdk", file=sys.stderr)
    sys.exit(1)


def get_client() -> WorkspaceClient:
    """Create and return a Databricks WorkspaceClient."""
    # Check if configured, offer setup if not
    host = os.environ.get("DATABRICKS_HOST", "")
    token = os.environ.get("DATABRICKS_TOKEN", "")

    if not host or not token:
        print("Databricks not configured.", file=sys.stderr)
        print("Run: python scripts/config_helper.py setup", file=sys.stderr)
        sys.exit(1)

    try:
        return WorkspaceClient()
    except Exception as e:
        print(f"Error: Failed to create Databricks client: {e}", file=sys.stderr)
        print("Run: python scripts/config_helper.py test", file=sys.stderr)
        sys.exit(1)


def list_catalogs() -> None:
    """List all accessible catalogs."""
    w = get_client()
    try:
        catalogs = list(w.catalogs.list())
        result = []
        for cat in catalogs:
            result.append({
                "name": cat.name,
                "comment": cat.comment,
                "owner": cat.owner,
                "catalog_type": cat.catalog_type.value if cat.catalog_type else None,
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error listing catalogs: {e}", file=sys.stderr)
        sys.exit(1)


def list_schemas(catalog_name: str) -> None:
    """List schemas in a catalog."""
    w = get_client()
    try:
        schemas = list(w.schemas.list(catalog_name=catalog_name))
        result = []
        for schema in schemas:
            result.append({
                "name": schema.name,
                "full_name": schema.full_name,
                "comment": schema.comment,
                "owner": schema.owner,
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error listing schemas in '{catalog_name}': {e}", file=sys.stderr)
        sys.exit(1)


def list_tables(catalog_name: str, schema_name: str) -> None:
    """List tables in a schema."""
    w = get_client()
    try:
        tables = list(w.tables.list(catalog_name=catalog_name, schema_name=schema_name))
        result = []
        for table in tables:
            result.append({
                "name": table.name,
                "full_name": table.full_name,
                "table_type": table.table_type.value if table.table_type else None,
                "data_source_format": table.data_source_format.value if table.data_source_format else None,
                "comment": table.comment,
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error listing tables in '{catalog_name}.{schema_name}': {e}", file=sys.stderr)
        sys.exit(1)


def get_table_schema(full_name: str) -> None:
    """Get detailed table schema with columns for code generation."""
    w = get_client()
    try:
        table = w.tables.get(full_name=full_name)
        columns = []
        for col in (table.columns or []):
            columns.append({
                "name": col.name,
                "type": col.type_text,
                "type_name": col.type_name.value if col.type_name else None,
                "nullable": col.nullable if col.nullable is not None else True,
                "comment": col.comment,
                "position": col.position,
            })

        result = {
            "name": table.name,
            "full_name": table.full_name,
            "catalog": table.catalog_name,
            "schema": table.schema_name,
            "table_type": table.table_type.value if table.table_type else None,
            "data_source_format": table.data_source_format.value if table.data_source_format else None,
            "comment": table.comment,
            "owner": table.owner,
            "columns": columns,
        }
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error getting table schema for '{full_name}': {e}", file=sys.stderr)
        sys.exit(1)


def get_table_ddl(full_name: str) -> None:
    """Generate CREATE TABLE DDL statement for a table."""
    w = get_client()
    try:
        table = w.tables.get(full_name=full_name)

        # Build column definitions
        col_defs = []
        for col in (table.columns or []):
            col_def = f"  {col.name} {col.type_text}"
            if col.nullable is False:
                col_def += " NOT NULL"
            if col.comment:
                col_def += f" COMMENT '{col.comment}'"
            col_defs.append(col_def)

        ddl = f"CREATE TABLE {table.full_name} (\n"
        ddl += ",\n".join(col_defs)
        ddl += "\n)"

        if table.comment:
            ddl += f"\nCOMMENT '{table.comment}'"

        print(ddl)
    except Exception as e:
        print(f"Error generating DDL for '{full_name}': {e}", file=sys.stderr)
        sys.exit(1)


def search_tables(catalog_name: str, pattern: str) -> None:
    """Search for tables matching a pattern."""
    w = get_client()
    try:
        summaries = list(w.tables.list_summaries(
            catalog_name=catalog_name,
            table_name_pattern=f"%{pattern}%"
        ))
        result = []
        for summary in summaries:
            result.append({
                "name": summary.table_name if hasattr(summary, 'table_name') else summary.name,
                "schema": summary.schema_name,
                "catalog": summary.catalog_name,
                "full_name": f"{summary.catalog_name}.{summary.schema_name}.{summary.table_name if hasattr(summary, 'table_name') else summary.name}",
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error searching tables: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Unity Catalog operations for schema access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s catalogs
  %(prog)s schemas main
  %(prog)s tables main default
  %(prog)s table-schema main.default.customers
  %(prog)s ddl main.default.customers
  %(prog)s search main customer
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Catalogs command
    subparsers.add_parser("catalogs", help="List all catalogs")

    # Schemas command
    schemas_parser = subparsers.add_parser("schemas", help="List schemas in a catalog")
    schemas_parser.add_argument("catalog", help="Catalog name")

    # Tables command
    tables_parser = subparsers.add_parser("tables", help="List tables in a schema")
    tables_parser.add_argument("catalog", help="Catalog name")
    tables_parser.add_argument("schema", help="Schema name")

    # Table-schema command
    schema_parser = subparsers.add_parser("table-schema", help="Get detailed table schema")
    schema_parser.add_argument("full_name", help="Full table name (catalog.schema.table)")

    # DDL command
    ddl_parser = subparsers.add_parser("ddl", help="Generate CREATE TABLE DDL")
    ddl_parser.add_argument("full_name", help="Full table name (catalog.schema.table)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search tables by name pattern")
    search_parser.add_argument("catalog", help="Catalog name")
    search_parser.add_argument("pattern", help="Table name pattern to search")

    args = parser.parse_args()

    if args.command == "catalogs":
        list_catalogs()
    elif args.command == "schemas":
        list_schemas(args.catalog)
    elif args.command == "tables":
        list_tables(args.catalog, args.schema)
    elif args.command == "table-schema":
        get_table_schema(args.full_name)
    elif args.command == "ddl":
        get_table_ddl(args.full_name)
    elif args.command == "search":
        search_tables(args.catalog, args.pattern)


if __name__ == "__main__":
    main()
