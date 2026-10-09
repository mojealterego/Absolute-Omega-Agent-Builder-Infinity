import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omega_builder.catalog import catalog_index, load_catalog, CatalogError
from omega_builder.selection import Selection, SelectionError, audit_catalogs, validate_selection


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_all_required_choice_types(self):
        catalog = catalog_index("build_types", "build_types")
        self.assertEqual(len(catalog), 10)
        self.assertTrue({"agent_code", "agent_nocode", "agent_hybrid", "meta_agent", "agent_system", "agent_orchestration", "agent_swarm", "agent_legion", "framework_fixed", "framework_mixed"}.issubset(catalog))

    def test_150_plus_unique_selectable_languages(self):
        values = catalog_index("languages", "languages")
        self.assertGreaterEqual(len(values), 150)
        for name in ("python", "rust", "go", "java", "typescript", "c-plus-plus", "c-sharp"):
            self.assertIn(name, values)
        self.assertTrue(all(v["status"] == "catalog_only" for v in values.values()))

    def test_framework_catalog_has_real_categories_not_live_capability_claim(self):
        values = catalog_index("frameworks", "frameworks")
        for name in ("langgraph", "crewai", "eclipse-zenoh", "microsoft-autogen", "mcp"):
            self.assertIn(name, values)
        self.assertTrue(all(x["integration"] == "not_connected" for x in values.values()))

    def test_zeus_hold_is_explicit(self):
        zeus = load_catalog("zeus_contract")
        self.assertEqual(zeus["implementation_status"], "ON_HOLD_AWAITING_USER_MATERIAL")
        self.assertEqual(zeus["generated_artifacts"], [])
        self.assertFalse(zeus["agent_file_created"])
        self.assertEqual(list(ROOT.rglob("AGENT.md")), [])

    def test_catalog_audit(self):
        audit = audit_catalogs()
        self.assertTrue(audit["ok"])
        self.assertEqual(audit["choices"], 10)

    def test_unknown_catalog_rejected(self):
        with self.assertRaises(CatalogError):
            load_catalog("../../.git/config")


class SelectionTests(unittest.TestCase):
    def test_code_example(self):
        result = validate_selection(Selection.from_dict(json.loads((ROOT / "examples" / "agent-code.json").read_text())))
        self.assertEqual(result["choice"]["language"], "rust")
        self.assertFalse(result["supported_now"])

    def test_nocode_example(self):
        result = validate_selection(Selection.from_dict(json.loads((ROOT / "examples" / "agent-nocode.json").read_text())))
        self.assertIsNone(result["choice"]["language"])

    def test_hybrid_example(self):
        result = validate_selection(Selection.from_dict(json.loads((ROOT / "examples" / "agent-hybrid.json").read_text())))
        self.assertEqual(result["choice"]["implementation"], "hybrid")

    def test_fixed_framework_needs_exactly_one(self):
        with self.assertRaisesRegex(SelectionError, "exactly one"):
            validate_selection(Selection("framework_fixed", "code", "fixed", (), language="python", target_build_type="agent_code"))

    def test_fixed_framework_requires_target(self):
        with self.assertRaisesRegex(SelectionError, "target_build_type"):
            validate_selection(Selection("framework_fixed", "code", "fixed", ("langgraph",), language="python"))

    def test_framework_mixed_with_target(self):
        result = validate_selection(Selection("framework_mixed", "code", "mixed", ("langgraph", "crewai"), language="python", target_build_type="agent_system"))
        self.assertEqual(len(result["choice"]["frameworks"]), 2)

    def test_framework_mixed_rejects_only_one(self):
        with self.assertRaisesRegex(SelectionError, "at least two"):
            validate_selection(Selection("framework_mixed", "code", "mixed", ("crewai",), language="python", target_build_type="agent_system"))

    def test_duplicate_framework_rejected(self):
        with self.assertRaisesRegex(SelectionError, "Duplicate"):
            validate_selection(Selection("agent_code", "code", "mixed", ("crewai", "crewai"), language="python"))

    def test_unknown_language_rejected(self):
        with self.assertRaisesRegex(SelectionError, "language"):
            validate_selection(Selection("agent_code", "code", "automatic", (), language="made-up-language"))

    def test_nocode_does_not_accept_language(self):
        with self.assertRaisesRegex(SelectionError, "must not claim"):
            validate_selection(Selection("agent_nocode", "nocode", "automatic", (), language="python", nocode_platform="n8n"))

    def test_unknown_fields_rejected(self):
        with self.assertRaisesRegex(SelectionError, "Unknown"):
            Selection.from_dict({"build_type": "agent_code", "zeus_run": True})

    def test_agent_nocode_platform_required(self):
        with self.assertRaisesRegex(SelectionError, "No-Code"):
            validate_selection(Selection("agent_nocode", "nocode", "automatic", ()))

    def test_root_zeus_cannot_be_generated(self):
        with self.assertRaisesRegex(SelectionError, "Unknown build_type"):
            validate_selection(Selection("zeus", "code", "automatic", (), language="python"))

    def test_cli_menu_is_json_and_no_agents(self):
        result = subprocess.run([sys.executable, "-m", "omega_builder", "menu"], cwd=ROOT, text=True, capture_output=True, check=True)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["choices"]), 10)
        self.assertEqual(data["zeus"], "ON_HOLD_AWAITING_USER_MATERIAL")

    def test_cli_rejects_unknown_language_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "no-write.json"
            run = subprocess.run([sys.executable, "-m", "omega_builder", "select", "--build-type", "agent_code", "--implementation", "code", "--language", "qwerty", "--output", str(path)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertFalse(path.exists())

    def test_cli_does_not_overwrite_existing_blueprint(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "existing.json"
            path.write_text("important user data", encoding="utf8")
            run = subprocess.run([sys.executable, "-m", "omega_builder", "select", "--build-type", "agent_code", "--implementation", "code", "--language", "rust", "--output", str(path)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(path.read_text(encoding="utf8"), "important user data")


if __name__ == "__main__":
    unittest.main()
