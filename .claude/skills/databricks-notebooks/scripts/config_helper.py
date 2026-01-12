#!/usr/bin/env python3
"""Configuration helper for Databricks skill.

This script helps check, create, and update the .env configuration file
for Databricks authentication.

Usage:
    python config_helper.py check          # Check current configuration
    python config_helper.py setup          # Interactive setup
    python config_helper.py set-host URL   # Set DATABRICKS_HOST
    python config_helper.py set-token TOKEN # Set DATABRICKS_TOKEN
    python config_helper.py test           # Test connection
"""

import argparse
import os
import sys
from pathlib import Path

# Find project root (where .env should be)
def find_project_root() -> Path:
    """Find project root by looking for .env or .git directory."""
    current = Path.cwd()

    # Check current directory first
    if (current / ".env").exists() or (current / ".git").exists():
        return current

    # Walk up to find project root
    for parent in current.parents:
        if (parent / ".env").exists() or (parent / ".git").exists():
            return parent

    # Default to current directory
    return current


def get_env_path() -> Path:
    """Get path to .env file."""
    return find_project_root() / ".env"


def load_env_file() -> dict:
    """Load and parse .env file."""
    env_path = get_env_path()
    env_vars = {}

    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip()

    return env_vars


def save_env_file(env_vars: dict) -> None:
    """Save environment variables to .env file."""
    env_path = get_env_path()

    lines = [
        "# Databricks Configuration",
        "# Managed by databricks-notebooks skill",
        "",
    ]

    for key, value in env_vars.items():
        lines.append(f"{key}={value}")

    lines.append("")  # Trailing newline

    with open(env_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Configuration saved to: {env_path}")


def get_current_config() -> dict:
    """Get current configuration from environment and .env file."""
    # Load from .env file
    file_vars = load_env_file()

    # Environment variables take precedence
    config = {
        "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST", file_vars.get("DATABRICKS_HOST", "")),
        "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN", file_vars.get("DATABRICKS_TOKEN", "")),
    }

    return config


def mask_token(token: str) -> str:
    """Mask token for display, showing only first and last 4 chars."""
    if not token:
        return "(not set)"
    if len(token) <= 12:
        return "****"
    return f"{token[:4]}...{token[-4:]}"


def check_config() -> bool:
    """Check current configuration status."""
    config = get_current_config()
    env_path = get_env_path()

    print("Databricks Configuration Status")
    print("=" * 40)
    print(f".env file: {env_path}")
    print(f"  exists: {env_path.exists()}")
    print()
    print("Variables:")
    print(f"  DATABRICKS_HOST:  {config['DATABRICKS_HOST'] or '(not set)'}")
    print(f"  DATABRICKS_TOKEN: {mask_token(config['DATABRICKS_TOKEN'])}")
    print()

    # Check if configuration is complete
    is_complete = bool(config["DATABRICKS_HOST"] and config["DATABRICKS_TOKEN"])

    if is_complete:
        print("Status: CONFIGURED")
        return True
    else:
        print("Status: INCOMPLETE")
        missing = []
        if not config["DATABRICKS_HOST"]:
            missing.append("DATABRICKS_HOST")
        if not config["DATABRICKS_TOKEN"]:
            missing.append("DATABRICKS_TOKEN")
        print(f"Missing: {', '.join(missing)}")
        print()
        print("Run 'python config_helper.py setup' to configure.")
        return False


def interactive_setup() -> None:
    """Interactive setup wizard."""
    print("Databricks Configuration Setup")
    print("=" * 40)
    print()

    config = get_current_config()

    # Get host
    current_host = config["DATABRICKS_HOST"]
    if current_host:
        print(f"Current DATABRICKS_HOST: {current_host}")
        host = input("New host (press Enter to keep current): ").strip()
        if not host:
            host = current_host
    else:
        print("Enter your Databricks workspace URL")
        print("  AWS:   https://dbc-xxxxxxxx-xxxx.cloud.databricks.com")
        print("  Azure: https://adb-xxxxxxxxx.x.azuredatabricks.net")
        print("  GCP:   https://xxxxxxxxx.gcp.databricks.com")
        host = input("DATABRICKS_HOST: ").strip()

    print()

    # Get token
    current_token = config["DATABRICKS_TOKEN"]
    if current_token:
        print(f"Current DATABRICKS_TOKEN: {mask_token(current_token)}")
        token = input("New token (press Enter to keep current): ").strip()
        if not token:
            token = current_token
    else:
        print("Enter your Personal Access Token")
        print("  Generate at: User Settings > Developer > Access Tokens")
        token = input("DATABRICKS_TOKEN: ").strip()

    # Validate
    if not host:
        print("\nError: DATABRICKS_HOST is required")
        sys.exit(1)
    if not token:
        print("\nError: DATABRICKS_TOKEN is required")
        sys.exit(1)

    # Save
    save_env_file({
        "DATABRICKS_HOST": host,
        "DATABRICKS_TOKEN": token,
    })

    print("\nConfiguration complete!")
    print("Run 'python config_helper.py test' to verify connection.")


def set_value(key: str, value: str) -> None:
    """Set a specific configuration value."""
    config = load_env_file()
    config[key] = value
    save_env_file(config)

    display_value = mask_token(value) if "TOKEN" in key else value
    print(f"Set {key}={display_value}")


def test_connection() -> bool:
    """Test connection to Databricks."""
    # Load .env first
    try:
        from dotenv import load_dotenv
        load_dotenv(get_env_path())
    except ImportError:
        pass

    config = get_current_config()

    if not config["DATABRICKS_HOST"] or not config["DATABRICKS_TOKEN"]:
        print("Error: Configuration incomplete. Run setup first.")
        return False

    print(f"Testing connection to {config['DATABRICKS_HOST']}...")

    try:
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient(
            host=config["DATABRICKS_HOST"],
            token=config["DATABRICKS_TOKEN"]
        )

        # Try to get current user
        user = w.current_user.me()
        print(f"Success! Connected as: {user.user_name}")
        return True

    except ImportError:
        print("Error: databricks-sdk not installed")
        print("Run: pip install databricks-sdk")
        return False
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def ensure_configured() -> bool:
    """Ensure configuration is complete, prompt setup if not.

    Returns True if configured, False otherwise.
    Call this from other scripts to auto-setup.
    """
    config = get_current_config()

    if config["DATABRICKS_HOST"] and config["DATABRICKS_TOKEN"]:
        return True

    print("Databricks not configured.")
    response = input("Run setup now? [Y/n]: ").strip().lower()

    if response in ("", "y", "yes"):
        interactive_setup()
        return True
    else:
        print("Setup skipped. Run 'python config_helper.py setup' later.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Databricks configuration helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check              # Check configuration status
  %(prog)s setup              # Interactive setup wizard
  %(prog)s set-host URL       # Set workspace URL
  %(prog)s set-token TOKEN    # Set access token
  %(prog)s test               # Test connection
"""
    )
    subparsers = parser.add_subparsers(dest="command")

    # Check command
    subparsers.add_parser("check", help="Check configuration status")

    # Setup command
    subparsers.add_parser("setup", help="Interactive setup wizard")

    # Set-host command
    host_parser = subparsers.add_parser("set-host", help="Set DATABRICKS_HOST")
    host_parser.add_argument("url", help="Databricks workspace URL")

    # Set-token command
    token_parser = subparsers.add_parser("set-token", help="Set DATABRICKS_TOKEN")
    token_parser.add_argument("token", help="Personal access token")

    # Test command
    subparsers.add_parser("test", help="Test connection")

    args = parser.parse_args()

    if args.command == "check" or args.command is None:
        check_config()
    elif args.command == "setup":
        interactive_setup()
    elif args.command == "set-host":
        set_value("DATABRICKS_HOST", args.url)
    elif args.command == "set-token":
        set_value("DATABRICKS_TOKEN", args.token)
    elif args.command == "test":
        success = test_connection()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
