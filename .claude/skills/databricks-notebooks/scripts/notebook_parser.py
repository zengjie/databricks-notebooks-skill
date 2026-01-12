#!/usr/bin/env python3
"""Parse and manipulate Databricks notebook SOURCE format.

This script handles cell-level operations on Databricks notebooks in SOURCE format.
SOURCE format uses '# COMMAND ----------' to separate cells and '# MAGIC' prefix
for non-default language content.

Usage:
    python notebook_parser.py parse < notebook.py
    python notebook_parser.py get-cell <index> < notebook.py
    python notebook_parser.py update-cell <index> --content "new code" < notebook.py
    python notebook_parser.py insert-cell <index> --content "code" [--language python] < notebook.py
    python notebook_parser.py delete-cell <index> < notebook.py
    python notebook_parser.py to-json < notebook.py
    python notebook_parser.py from-json < notebook.json
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import List, Optional


CELL_DELIMITER = "# COMMAND ----------"
MAGIC_PREFIX = "# MAGIC "
NOTEBOOK_HEADER = "# Databricks notebook source"


@dataclass
class Cell:
    """Represents a single notebook cell."""
    index: int
    content: str
    language: Optional[str] = None  # None means default notebook language

    def to_dict(self):
        return {
            "index": self.index,
            "content": self.content,
            "language": self.language,
        }


def detect_cell_language(content: str) -> Optional[str]:
    """Detect the language of a cell from MAGIC commands."""
    lines = content.strip().split("\n")
    if not lines:
        return None

    first_line = lines[0].strip()
    if first_line.startswith(MAGIC_PREFIX):
        magic_content = first_line[len(MAGIC_PREFIX):].strip()
        if magic_content.startswith("%"):
            lang = magic_content[1:].split()[0] if magic_content[1:] else None
            if lang in ("python", "sql", "scala", "r", "md", "sh", "fs", "run", "pip"):
                return lang
    return None


def parse_cells(content: str) -> List[Cell]:
    """Parse notebook content into cells."""
    # Remove header if present
    if content.startswith(NOTEBOOK_HEADER):
        content = content[len(NOTEBOOK_HEADER):].lstrip("\n")

    # Split by cell delimiter
    raw_cells = content.split(CELL_DELIMITER)

    cells = []
    for i, raw_cell in enumerate(raw_cells):
        # Clean up cell content
        cell_content = raw_cell.strip()
        if not cell_content and i > 0:
            continue  # Skip empty cells (except first one which might be intentional)

        language = detect_cell_language(cell_content)
        cells.append(Cell(
            index=len(cells),
            content=cell_content,
            language=language,
        ))

    return cells


def cells_to_source(cells: List[Cell], include_header: bool = True) -> str:
    """Convert cells back to SOURCE format."""
    parts = []

    if include_header:
        parts.append(NOTEBOOK_HEADER)

    for i, cell in enumerate(cells):
        if i > 0 or include_header:
            parts.append("")
            parts.append(CELL_DELIMITER)
            parts.append("")
        parts.append(cell.content)

    return "\n".join(parts)


def format_cell_display(cell: Cell, show_content: bool = True) -> str:
    """Format a cell for display."""
    lang_str = f" [{cell.language}]" if cell.language else ""
    header = f"--- Cell {cell.index}{lang_str} ---"

    if show_content:
        # Show preview of content
        lines = cell.content.split("\n")
        preview_lines = lines[:10]
        if len(lines) > 10:
            preview_lines.append(f"... ({len(lines) - 10} more lines)")
        content = "\n".join(preview_lines)
        return f"{header}\n{content}"
    else:
        line_count = len(cell.content.split("\n"))
        return f"{header} ({line_count} lines)"


def wrap_as_magic(content: str, language: str) -> str:
    """Wrap content with MAGIC prefix for non-default language cells."""
    if language in ("md", "sql", "scala", "r", "sh", "fs", "run", "pip"):
        lines = content.split("\n")
        wrapped = [f"# MAGIC %{language}"]
        for line in lines:
            wrapped.append(f"# MAGIC {line}" if line else "# MAGIC")
        return "\n".join(wrapped)
    return content


def unwrap_magic(content: str) -> str:
    """Remove MAGIC prefix from cell content."""
    lines = content.split("\n")
    unwrapped = []
    for line in lines:
        if line.startswith(MAGIC_PREFIX):
            unwrapped.append(line[len(MAGIC_PREFIX):])
        elif line.strip() == "# MAGIC":
            unwrapped.append("")
        else:
            unwrapped.append(line)

    # Remove language directive from first line if present
    if unwrapped and unwrapped[0].startswith("%"):
        unwrapped = unwrapped[1:]

    return "\n".join(unwrapped).strip()


def cmd_parse(args):
    """Parse notebook and display cells."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    if args.json:
        print(json.dumps([c.to_dict() for c in cells], indent=2))
    else:
        for cell in cells:
            print(format_cell_display(cell, show_content=not args.summary))
            print()


def cmd_get_cell(args):
    """Get a specific cell by index."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    if args.index < 0 or args.index >= len(cells):
        print(f"Error: Cell index {args.index} out of range (0-{len(cells)-1})", file=sys.stderr)
        sys.exit(1)

    cell = cells[args.index]
    if args.json:
        print(json.dumps(cell.to_dict(), indent=2))
    elif args.raw:
        print(cell.content)
    else:
        print(format_cell_display(cell))


def cmd_update_cell(args):
    """Update a specific cell's content."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    if args.index < 0 or args.index >= len(cells):
        print(f"Error: Cell index {args.index} out of range (0-{len(cells)-1})", file=sys.stderr)
        sys.exit(1)

    # Read new content from file or argument
    if args.content_file:
        with open(args.content_file, "r") as f:
            new_content = f.read().strip()
    else:
        new_content = args.content

    if new_content is None:
        print("Error: Must provide --content or --content-file", file=sys.stderr)
        sys.exit(1)

    # Wrap with MAGIC if language specified
    if args.language:
        new_content = wrap_as_magic(new_content, args.language)
        cells[args.index].language = args.language

    cells[args.index].content = new_content
    print(cells_to_source(cells))


def cmd_insert_cell(args):
    """Insert a new cell at specified index."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    if args.index < 0 or args.index > len(cells):
        print(f"Error: Insert index {args.index} out of range (0-{len(cells)})", file=sys.stderr)
        sys.exit(1)

    # Read content
    if args.content_file:
        with open(args.content_file, "r") as f:
            new_content = f.read().strip()
    else:
        new_content = args.content

    if new_content is None:
        print("Error: Must provide --content or --content-file", file=sys.stderr)
        sys.exit(1)

    # Wrap with MAGIC if language specified
    language = None
    if args.language:
        new_content = wrap_as_magic(new_content, args.language)
        language = args.language

    new_cell = Cell(index=args.index, content=new_content, language=language)
    cells.insert(args.index, new_cell)

    # Re-index cells
    for i, cell in enumerate(cells):
        cell.index = i

    print(cells_to_source(cells))


def cmd_delete_cell(args):
    """Delete a cell at specified index."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    if args.index < 0 or args.index >= len(cells):
        print(f"Error: Cell index {args.index} out of range (0-{len(cells)-1})", file=sys.stderr)
        sys.exit(1)

    del cells[args.index]

    # Re-index cells
    for i, cell in enumerate(cells):
        cell.index = i

    print(cells_to_source(cells))


def cmd_to_json(_args):
    """Convert notebook to JSON representation."""
    content = sys.stdin.read()
    cells = parse_cells(content)

    output = {
        "format": "databricks-source",
        "cells": [c.to_dict() for c in cells],
    }
    print(json.dumps(output, indent=2))


def cmd_from_json(_args):
    """Convert JSON representation back to SOURCE format."""
    data = json.load(sys.stdin)

    cells = [
        Cell(
            index=c.get("index", i),
            content=c["content"],
            language=c.get("language"),
        )
        for i, c in enumerate(data.get("cells", []))
    ]

    print(cells_to_source(cells))


def cmd_count(_args):
    """Count cells in notebook."""
    content = sys.stdin.read()
    cells = parse_cells(content)
    print(len(cells))


def main():
    parser = argparse.ArgumentParser(
        description="Parse and manipulate Databricks notebook SOURCE format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse notebook and display cells")
    parse_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parse_parser.add_argument("--summary", "-s", action="store_true", help="Show summary only")

    # Get-cell command
    get_parser = subparsers.add_parser("get-cell", help="Get a specific cell")
    get_parser.add_argument("index", type=int, help="Cell index (0-based)")
    get_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    get_parser.add_argument("--raw", "-r", action="store_true", help="Output raw content only")

    # Update-cell command
    update_parser = subparsers.add_parser("update-cell", help="Update a cell's content")
    update_parser.add_argument("index", type=int, help="Cell index (0-based)")
    update_parser.add_argument("--content", "-c", help="New cell content")
    update_parser.add_argument("--content-file", "-f", help="File containing new content")
    update_parser.add_argument("--language", "-l", help="Cell language (adds MAGIC prefix)")

    # Insert-cell command
    insert_parser = subparsers.add_parser("insert-cell", help="Insert a new cell")
    insert_parser.add_argument("index", type=int, help="Insert position (0-based)")
    insert_parser.add_argument("--content", "-c", help="Cell content")
    insert_parser.add_argument("--content-file", "-f", help="File containing content")
    insert_parser.add_argument("--language", "-l", help="Cell language (adds MAGIC prefix)")

    # Delete-cell command
    delete_parser = subparsers.add_parser("delete-cell", help="Delete a cell")
    delete_parser.add_argument("index", type=int, help="Cell index to delete (0-based)")

    # To-json command
    subparsers.add_parser("to-json", help="Convert notebook to JSON")

    # From-json command
    subparsers.add_parser("from-json", help="Convert JSON back to SOURCE format")

    # Count command
    subparsers.add_parser("count", help="Count cells in notebook")

    args = parser.parse_args()

    commands = {
        "parse": cmd_parse,
        "get-cell": cmd_get_cell,
        "update-cell": cmd_update_cell,
        "insert-cell": cmd_insert_cell,
        "delete-cell": cmd_delete_cell,
        "to-json": cmd_to_json,
        "from-json": cmd_from_json,
        "count": cmd_count,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
