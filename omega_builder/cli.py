"""Offline catalogue explorer and blueprint selector: no implicit code execution."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import CatalogError, catalog_index, load_catalog
from .selection import Selection, SelectionError, audit_catalogs, validate_selection
from .mathematics.api import OPERATIONS, calculate, MathAPIError
from .mcp_registry import (
    MCPRegistryError, ingest_page, normalize_entry, assess_candidate,
    registry_list_query, plan_tool_descriptors,
)


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
    cmd.add_parser("math-ops", help="List offline, whitelist-verified math primitives")
    m = cmd.add_parser("math", help="Run one JSON math problem")
    m.add_argument("config", type=Path)
    mcp_url = cmd.add_parser("mcp-registry-url", help="Plan official MCP Registry v0.1 URL (NO network)")
    mcp_url.add_argument("--search")
    mcp_url.add_argument("--cursor")
    mcp_url.add_argument("--updated-since")
    mcp_intake = cmd.add_parser("mcp-intake", help="Normalize offline MCP Registry JSON page; NO installs")
    mcp_intake.add_argument("config", type=Path)
    mcp_assess = cmd.add_parser("mcp-assess", help="Assess one MCP candidate with user-supplied evidence")
    mcp_assess.add_argument("config", type=Path)
    mcp_tools = cmd.add_parser("mcp-tool-plan", help="Produce allowlisted tool schemas only, no tool calls")
    mcp_tools.add_argument("config", type=Path)
    cmd.add_parser("mcp-sources", help="Show research source catalogue (reported figures unverified)")
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
        elif args.command == "math-ops":
            _print_json({"operations": sorted(OPERATIONS), "scope": "offline bounded mathematical methods"})
        elif args.command == "math":
            if args.config.stat().st_size > 128 * 1024:
                raise MathAPIError("Math input too large (128 KiB max)")
            _print_json(calculate(json.loads(args.config.read_text(encoding="utf-8"))))
        elif args.command == "mcp-registry-url":
            _print_json({"url": registry_list_query(args.search, args.cursor, args.updated_since),
                         "network_requested": False})
        elif args.command == "mcp-sources":
            _print_json(load_catalog("mcp_ecosystem_sources"))
        elif args.command in {"mcp-intake", "mcp-assess", "mcp-tool-plan"}:
            if args.config.stat().st_size > 1024 * 1024:
                raise MCPRegistryError("MCP JSON input limited to 1 MiB")
            data = json.loads(args.config.read_text(encoding="utf-8"))
            if args.command == "mcp-intake":
                _print_json(ingest_page(data))
            elif args.command == "mcp-assess":
                if not isinstance(data, dict) or set(data) != {"entry", "evidence"}:
                    raise MCPRegistryError("mcp-assess requires entry and evidence")
                _print_json(assess_candidate(normalize_entry(data["entry"]), data["evidence"]))
            elif args.command == "mcp-tool-plan":
                if not isinstance(data, dict) or set(data) != {"manifest", "allowlist", "max_tools"}:
                    raise MCPRegistryError("mcp-tool-plan requires manifest, allowlist and max_tools")
                _print_json(plan_tool_descriptors(data["manifest"], data["allowlist"], data["max_tools"]))
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
    except (CatalogError, SelectionError, MathAPIError, MCPRegistryError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
