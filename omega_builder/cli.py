"""Offline catalogue explorer and blueprint selector: no implicit code execution."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import CatalogError, catalog_index, load_catalog
from .selection import Selection, SelectionError, audit_catalogs, validate_selection


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-builder", description="Absolute Omega Agent Builder Infinity (selection architecture, Zeus on hold)")
    cmd = parser.add_subparsers(dest="command", required=True)
    cmd.add_parser("menu", help="Show ten main builder choices")
    languages = cmd.add_parser("languages", help="List 150+ catalogued languages (not compiled adapters)")
    languages.add_argument("--count", action="store_true")
    frameworks = cmd.add_parser("frameworks", help="List framework/transport/evaluation candidates")
    frameworks.add_argument("--category", type=str)
    cmd.add_parser("catalog-audit", help="Verify catalog integrity and Zeus hold")
    validate = cmd.add_parser("validate", help="Validate selection JSON and print blueprint")
    validate.add_argument("config", type=Path)
    select = cmd.add_parser("select", help="Create selection blueprint only; DOES NOT build agents")
    select.add_argument("--build-type", required=True)
    select.add_argument("--implementation", required=True, choices=["code", "nocode", "hybrid"])
    select.add_argument("--language")
    select.add_argument("--nocode-platform")
    select.add_argument("--framework-mode", choices=["automatic", "fixed", "mixed"], default="automatic")
    select.add_argument("--framework", action="append", default=[])
    select.add_argument("--target-build-type")
    select.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "menu":
            data = load_catalog("build_types")
            _print_json({"choices": data["build_types"], "zeus": "ON_HOLD_AWAITING_USER_MATERIAL"})
        elif args.command == "languages":
            data = load_catalog("languages")["languages"]
            _print_json({"catalogued_languages": len(data)}) if args.count else _print_json(data)
        elif args.command == "frameworks":
            data = load_catalog("frameworks")["frameworks"]
            _print_json([item for item in data if not args.category or item["category"] == args.category])
        elif args.command == "catalog-audit":
            _print_json(audit_catalogs())
        elif args.command == "validate":
            selection = Selection.from_dict(json.loads(args.config.read_text(encoding="utf-8")))
            _print_json(validate_selection(selection))
        elif args.command == "select":
            selection = Selection.from_dict({
                "build_type": args.build_type,
                "implementation": args.implementation,
                "language": args.language,
                "nocode_platform": args.nocode_platform,
                "framework_mode": args.framework_mode,
                "frameworks": args.framework,
                "target_build_type": args.target_build_type,
            })
            result = validate_selection(selection)
            if args.output:
                if args.output.exists():
                    raise SelectionError(f"Refusing to overwrite existing file: {args.output}")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"Saved selection blueprint: {args.output}")
            else:
                _print_json(result)
        return 0
    except (CatalogError, SelectionError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
