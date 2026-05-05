"""
setup_workspace.py
CPython 3.x — run BEFORE any CODESYS.exe invocation.

Usage:
    python setup_workspace.py <template_name> <workspace_name> [--registry <path>]

Example:
    python setup_workspace.py pdm360 MyNewProject_2024

Output (stdout, one line each):
    PROJECT_PATH=C:\\codesys-workspaces\\MyNewProject_2024\\MyNewProject_2024.project
    CODESYS_EXE=C:\\Program Files\\...\\CODESYS.exe
    CODESYS_PROFILE=CODESYS V3.5 SP17 Patch 20
    WORKSPACE=C:\\codesys-workspaces\\MyNewProject_2024

Caller (batch script) captures these with `for /f` to pass into subsequent steps.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).parent / "templates.json"


def load_registry(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="Template name from registry (e.g. pdm360)")
    parser.add_argument("workspace_name", help="Name for the new workspace folder")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--list", action="store_true", help="List available templates and exit")
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))

    if args.list:
        print("Available templates:")
        for name, meta in registry["templates"].items():
            print(f"  {name:20s} — {meta['description']}")
            print(f"  {'':20s}   project: {meta['project']}")
        sys.exit(0)

    templates = registry["templates"]
    defaults = registry["defaults"]

    if args.template not in templates:
        print(f"ERROR: Template '{args.template}' not found.", file=sys.stderr)
        print(f"Available: {', '.join(templates.keys())}", file=sys.stderr)
        sys.exit(1)

    tmpl = templates[args.template]
    src_project = Path(tmpl["project"])

    if not src_project.exists():
        print(f"ERROR: Template file not found: {src_project}", file=sys.stderr)
        sys.exit(2)

    # Create workspace directory
    workspace = Path(defaults["workspace_root"]) / args.workspace_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Copy .project with workspace name
    dst_project = workspace / f"{args.workspace_name}.project"
    shutil.copy2(src_project, dst_project)

    # Emit key=value pairs for batch script consumption
    print(f"PROJECT_PATH={dst_project}")
    print(f"CODESYS_EXE={defaults['codesys_exe']}")
    print(f"CODESYS_PROFILE={tmpl['codesys_profile']}")
    print(f"WORKSPACE={workspace}")


if __name__ == "__main__":
    main()
