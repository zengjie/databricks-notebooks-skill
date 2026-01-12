#!/usr/bin/env python3
"""Databricks notebook operations for Claude Code skill.

This script provides CLI commands for interacting with Databricks notebooks
via the Workspace API.

Usage:
    python databricks_client.py list <path>
    python databricks_client.py export <path> [--format FORMAT]
    python databricks_client.py import <path> --content-file FILE --language LANG
    python databricks_client.py status <path>
    python databricks_client.py delete <path> [--recursive]

Environment:
    DATABRICKS_HOST: Workspace URL (e.g., https://xxx.cloud.databricks.com)
    DATABRICKS_TOKEN: Personal access token
"""

import argparse
import base64
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
    from databricks.sdk.service.workspace import (
        ExportFormat,
        ImportFormat,
        Language,
    )
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


def list_workspace(path: str) -> None:
    """List contents of a workspace directory."""
    w = get_client()
    try:
        objects = list(w.workspace.list(path=path))
        result = []
        for obj in objects:
            item = {
                "path": obj.path,
                "type": obj.object_type.value if obj.object_type else None,
            }
            if obj.language:
                item["language"] = obj.language.value
            if obj.object_id:
                item["object_id"] = obj.object_id
            result.append(item)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error listing workspace: {e}", file=sys.stderr)
        sys.exit(1)


def export_notebook(path: str, format_str: str = "SOURCE") -> None:
    """Export a notebook's content."""
    w = get_client()
    try:
        fmt = ExportFormat[format_str.upper()]
        response = w.workspace.export(path=path, format=fmt)
        if response.content:
            content = base64.b64decode(response.content).decode("utf-8")
            print(content)
        else:
            print("Warning: Notebook is empty", file=sys.stderr)
    except KeyError:
        print(f"Error: Invalid format '{format_str}'. Use: SOURCE, JUPYTER, HTML, DBC, R_MARKDOWN", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error exporting notebook: {e}", file=sys.stderr)
        sys.exit(1)


def verify_import(w: WorkspaceClient, path: str, expected_content: str) -> tuple[bool, str]:
    """Verify that the imported content matches expected content."""
    try:
        response = w.workspace.export(path=path, format=ExportFormat.SOURCE)
        if response.content:
            actual_content = base64.b64decode(response.content).decode("utf-8")
            # Normalize line endings for comparison
            expected_normalized = expected_content.strip().replace('\r\n', '\n')
            actual_normalized = actual_content.strip().replace('\r\n', '\n')
            if expected_normalized == actual_normalized:
                return True, ""
            else:
                # Return first difference for debugging
                exp_lines = expected_normalized.split('\n')
                act_lines = actual_normalized.split('\n')
                for i, (exp, act) in enumerate(zip(exp_lines, act_lines)):
                    if exp != act:
                        return False, f"Line {i+1} differs:\n  Expected: {exp[:80]}\n  Actual:   {act[:80]}"
                if len(exp_lines) != len(act_lines):
                    return False, f"Line count differs: expected {len(exp_lines)}, got {len(act_lines)}"
                return False, "Content differs (unknown reason)"
        return False, "Exported content is empty"
    except Exception as e:
        return False, f"Verification failed: {e}"


def import_notebook(
    path: str,
    content_file: str,
    language: str,
    overwrite: bool = True,
    verify: bool = True
) -> None:
    """Import/create a notebook from a file."""
    w = get_client()
    try:
        lang = Language[language.upper()]
    except KeyError:
        print(f"Error: Invalid language '{language}'. Use: PYTHON, SQL, SCALA, R", file=sys.stderr)
        sys.exit(1)

    try:
        with open(content_file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Content file not found: {content_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading content file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        encoded = base64.b64encode(content.encode()).decode()
        w.workspace.import_(
            path=path,
            content=encoded,
            format=ImportFormat.SOURCE,
            language=lang,
            overwrite=overwrite,
        )

        # Verify the import
        if verify:
            success, error_msg = verify_import(w, path, content)
            if success:
                print(json.dumps({"status": "success", "path": path, "language": language, "verified": True}))
            else:
                print(json.dumps({
                    "status": "warning",
                    "path": path,
                    "language": language,
                    "verified": False,
                    "verification_error": error_msg
                }))
                print(f"Warning: Content verification failed: {error_msg}", file=sys.stderr)
        else:
            print(json.dumps({"status": "success", "path": path, "language": language}))
    except Exception as e:
        print(f"Error importing notebook: {e}", file=sys.stderr)
        sys.exit(1)


def import_from_stdin(
    path: str,
    language: str,
    overwrite: bool = True,
    verify: bool = True
) -> None:
    """Import/create a notebook from stdin."""
    w = get_client()
    try:
        lang = Language[language.upper()]
    except KeyError:
        print(f"Error: Invalid language '{language}'. Use: PYTHON, SQL, SCALA, R", file=sys.stderr)
        sys.exit(1)

    try:
        content = sys.stdin.read()
    except Exception as e:
        print(f"Error reading from stdin: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        encoded = base64.b64encode(content.encode()).decode()
        w.workspace.import_(
            path=path,
            content=encoded,
            format=ImportFormat.SOURCE,
            language=lang,
            overwrite=overwrite,
        )

        # Verify the import
        if verify:
            success, error_msg = verify_import(w, path, content)
            if success:
                print(json.dumps({"status": "success", "path": path, "language": language, "verified": True}))
            else:
                print(json.dumps({
                    "status": "warning",
                    "path": path,
                    "language": language,
                    "verified": False,
                    "verification_error": error_msg
                }))
                print(f"Warning: Content verification failed: {error_msg}", file=sys.stderr)
        else:
            print(json.dumps({"status": "success", "path": path, "language": language}))
    except Exception as e:
        print(f"Error importing notebook: {e}", file=sys.stderr)
        sys.exit(1)


def get_status(path: str) -> None:
    """Get metadata about a notebook or directory."""
    w = get_client()
    try:
        status = w.workspace.get_status(path=path)
        result = {
            "path": status.path,
            "type": status.object_type.value if status.object_type else None,
            "object_id": status.object_id,
        }
        if status.language:
            result["language"] = status.language.value
        if status.created_at:
            result["created_at"] = status.created_at
        if status.modified_at:
            result["modified_at"] = status.modified_at
        if status.size:
            result["size"] = status.size
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error getting status: {e}", file=sys.stderr)
        sys.exit(1)


def delete_object(path: str, recursive: bool = False) -> None:
    """Delete a notebook or directory."""
    w = get_client()
    try:
        w.workspace.delete(path=path, recursive=recursive)
        print(json.dumps({"status": "deleted", "path": path}))
    except Exception as e:
        print(f"Error deleting object: {e}", file=sys.stderr)
        sys.exit(1)


def create_directory(path: str) -> None:
    """Create a directory in the workspace."""
    w = get_client()
    try:
        w.workspace.mkdirs(path=path)
        print(json.dumps({"status": "created", "path": path, "type": "DIRECTORY"}))
    except Exception as e:
        print(f"Error creating directory: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Databricks notebook operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list /Users/user@example.com/
  %(prog)s export /Users/user@example.com/notebook
  %(prog)s import /Users/user@example.com/notebook -f content.py -l PYTHON
  %(prog)s status /Users/user@example.com/notebook
  %(prog)s delete /Users/user@example.com/notebook
  %(prog)s mkdir /Users/user@example.com/new-folder
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List workspace directory contents")
    list_parser.add_argument("path", help="Workspace path to list")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export notebook content")
    export_parser.add_argument("path", help="Notebook path")
    export_parser.add_argument(
        "--format", "-f",
        default="SOURCE",
        choices=["SOURCE", "JUPYTER", "HTML", "DBC", "R_MARKDOWN"],
        help="Export format (default: SOURCE)"
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import/create notebook")
    import_parser.add_argument("path", help="Target notebook path")
    import_parser.add_argument(
        "--content-file", "-f",
        help="File containing notebook content (omit to read from stdin)"
    )
    import_parser.add_argument(
        "--language", "-l",
        required=True,
        choices=["PYTHON", "SQL", "SCALA", "R"],
        help="Notebook language"
    )
    import_parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if notebook already exists"
    )
    import_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification after import"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get notebook/directory metadata")
    status_parser.add_argument("path", help="Object path")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete notebook or directory")
    delete_parser.add_argument("path", help="Object path to delete")
    delete_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively delete directory contents"
    )

    # Mkdir command
    mkdir_parser = subparsers.add_parser("mkdir", help="Create a directory")
    mkdir_parser.add_argument("path", help="Directory path to create")

    args = parser.parse_args()

    if args.command == "list":
        list_workspace(args.path)
    elif args.command == "export":
        export_notebook(args.path, args.format)
    elif args.command == "import":
        if args.content_file:
            import_notebook(args.path, args.content_file, args.language, not args.no_overwrite, not args.no_verify)
        else:
            import_from_stdin(args.path, args.language, not args.no_overwrite, not args.no_verify)
    elif args.command == "status":
        get_status(args.path)
    elif args.command == "delete":
        delete_object(args.path, args.recursive)
    elif args.command == "mkdir":
        create_directory(args.path)


if __name__ == "__main__":
    main()
