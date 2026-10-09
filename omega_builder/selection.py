"""Contract validation and immutable blueprint planning for user choices.

This module deliberately DOES NOT instantiate an agent, nor does it implement Zeus.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .catalog import CatalogError, catalog_index, load_catalog


BUILD_MODES = frozenset({"code", "nocode", "hybrid"})
FRAMEWORK_MODES = frozenset({"automatic", "fixed", "mixed"})


class SelectionError(ValueError):
    """Unsupported or inconsistent builder selection."""


@dataclass(frozen=True)
class Selection:
    build_type: str
    implementation: str
    framework_mode: str
    frameworks: tuple[str, ...]
    language: str | None = None
    nocode_platform: str | None = None
    target_build_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Selection":
        if not isinstance(data, dict):
            raise SelectionError("Selection must be an object")
        allowed = {"build_type", "implementation", "framework_mode", "frameworks", "language", "nocode_platform", "target_build_type"}
        extra = set(data) - allowed
        if extra:
            raise SelectionError(f"Unknown selection fields: {', '.join(sorted(extra))}")
        frameworks = data.get("frameworks", [])
        if not isinstance(frameworks, list) or not all(isinstance(x, str) and x for x in frameworks):
            raise SelectionError("frameworks must be a list of non-empty identifiers")
        return cls(
            build_type=data.get("build_type", ""),
            implementation=data.get("implementation", ""),
            framework_mode=data.get("framework_mode", "automatic"),
            frameworks=tuple(frameworks),
            language=data.get("language"),
            nocode_platform=data.get("nocode_platform"),
            target_build_type=data.get("target_build_type"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_type": self.build_type,
            "implementation": self.implementation,
            "framework_mode": self.framework_mode,
            "frameworks": list(self.frameworks),
            "language": self.language,
            "nocode_platform": self.nocode_platform,
            "target_build_type": self.target_build_type,
        }


def validate_selection(choice: Selection) -> dict[str, Any]:
    """Ensure selections are catalog-backed and compatible; no arbitrary defaults."""
    build_types = catalog_index("build_types", "build_types")
    languages = catalog_index("languages", "languages")
    frameworks = catalog_index("frameworks", "frameworks")
    if choice.build_type not in build_types:
        raise SelectionError(f"Unknown build_type: {choice.build_type}")
    if choice.implementation not in BUILD_MODES:
        raise SelectionError("implementation must be code, nocode or hybrid")
    if choice.framework_mode not in FRAMEWORK_MODES:
        raise SelectionError("framework_mode must be automatic, fixed or mixed")
    descriptor = build_types[choice.build_type]
    if choice.implementation not in descriptor["allowed_implementations"]:
        raise SelectionError(f"Build type {choice.build_type} does not allow {choice.implementation}")
    if descriptor["kind"] == "framework_policy":
        expected = "fixed" if choice.build_type == "framework_fixed" else "mixed"
        if choice.framework_mode != expected:
            raise SelectionError(f"{choice.build_type} requires framework_mode={expected}")
        if choice.target_build_type not in build_types or build_types[choice.target_build_type]["kind"] != "artifact":
            raise SelectionError("Framework policy requires an existing artifact target_build_type")
        target = build_types[choice.target_build_type]
        if choice.implementation not in target["allowed_implementations"]:
            raise SelectionError("Target does not support the chosen implementation")
    elif choice.target_build_type is not None:
        raise SelectionError("target_build_type is allowed only for framework policy choices")
    if choice.implementation in {"code", "hybrid"}:
        if not isinstance(choice.language, str) or choice.language not in languages:
            raise SelectionError("Choose a language ID from the languages catalog")
    elif choice.language is not None:
        raise SelectionError("No-Code choice must not claim a programming language implementation")
    nocode_platforms = set(load_catalog("build_types")["nocode_platforms"])
    if choice.implementation in {"nocode", "hybrid"}:
        if choice.nocode_platform not in nocode_platforms:
            raise SelectionError("Choose a supported No-Code export target")
    elif choice.nocode_platform is not None:
        raise SelectionError("Code-only choice must not set nocode_platform")
    if len(set(choice.frameworks)) != len(choice.frameworks):
        raise SelectionError("Duplicate framework entries")
    if any(f not in frameworks for f in choice.frameworks):
        raise SelectionError("Unknown framework: " + ", ".join(f for f in choice.frameworks if f not in frameworks))
    if choice.framework_mode == "fixed" and len(choice.frameworks) != 1:
        raise SelectionError("fixed mode requires exactly one framework")
    if choice.framework_mode == "mixed" and len(choice.frameworks) < 2:
        raise SelectionError("mixed mode requires at least two frameworks")
    if choice.framework_mode == "automatic" and choice.frameworks:
        raise SelectionError("automatic mode does not accept manually selected frameworks")
    return {
        "choice": choice.to_dict(),
        "catalogue_language_status": languages[choice.language]["status"] if choice.language else None,
        "framework_statuses": {f: frameworks[f]["status"] for f in choice.frameworks},
        "supported_now": False,
        "delivery_stage": "selection_blueprint_only",
        "requires": ["provider/runtime verification", "implementation", "tests", "security gates", "explicit approval before deployment"],
        "zeus": "specification_hold_do_not_implement",
    }


def audit_catalogs() -> dict[str, Any]:
    """Detect malformed registries and missing cross-catalog references."""
    modes = catalog_index("build_types", "build_types")
    languages = catalog_index("languages", "languages")
    frameworks = catalog_index("frameworks", "frameworks")
    if len(modes) != 10:
        raise CatalogError(f"Expected 10 user choices; got {len(modes)}")
    if len(languages) < 150:
        raise CatalogError(f"Expected >=150 language identifiers, got {len(languages)}")
    if not {"agent_code", "agent_nocode", "agent_hybrid", "meta_agent", "agent_system", "agent_orchestration", "agent_swarm", "agent_legion", "framework_fixed", "framework_mixed"} == set(modes):
        raise CatalogError("Choice IDs inconsistent with required taxonomy")
    for lang in languages.values():
        if lang.get("status") not in {"catalog_only", "verified_adapter"}:
            raise CatalogError("Unknown language support status")
    zeus = load_catalog("zeus_contract")
    if zeus.get("implementation_status") != "ON_HOLD_AWAITING_USER_MATERIAL":
        raise CatalogError("Zeus hold gate has been changed")
    if zeus.get("generated_artifacts") != []:
        raise CatalogError("Zeus artifacts must be empty until explicit release")
    return {"ok": True, "choices": len(modes), "catalogued_languages": len(languages), "frameworks": len(frameworks), "zeus_status": zeus["implementation_status"]}
