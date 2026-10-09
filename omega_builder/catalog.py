"""Typed, fail-closed access to the architecture choice registries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"


class CatalogError(ValueError):
    """Configuration or catalog validation failure."""


def load_catalog(name: str) -> dict[str, Any]:
    """Load only one of the declared catalog files from the repository root."""
    allowed = {"build_types", "languages", "frameworks", "capabilities", "infrastructure", "zeus_contract", "mars_variants"}
    if name not in allowed:
        raise CatalogError(f"Unknown catalog: {name}")
    path = CATALOG / f"{name}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Cannot read {name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CatalogError(f"Catalog {name} is not an object")
    return payload


def catalog_index(name: str, field: str) -> dict[str, dict[str, Any]]:
    """Return unique objects indexed by stable ID, validating core integrity."""
    data = load_catalog(name)
    values = data.get(field)
    if not isinstance(values, list):
        raise CatalogError(f"Catalog {name} missing array {field}")
    found: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not value["id"]:
            raise CatalogError(f"Invalid entry in {name}.{field}")
        if value["id"] in found:
            raise CatalogError(f"Duplicate ID {value['id']} in {name}.{field}")
        found[value["id"]] = value
    return found
