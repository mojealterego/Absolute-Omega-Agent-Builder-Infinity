"""CLI integration tests for MCP discovery: no external service calls."""
import contextlib
import io
import json
from pathlib import Path
import unittest

from omega_builder.cli import main,build_parser


ROOT=Path(__file__).resolve().parents[1]

class MCPCliTests(unittest.TestCase):
    def invoke(self,args):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            status=main(args)
        return status,json.loads(output.getvalue())

    def test_registry_plan_url(self):
        status,out=self.invoke(["mcp-registry-url","--search","filesystem"])
        self.assertEqual(status,0)
        self.assertFalse(out["network_requested"])
        self.assertIn("search=filesystem",out["url"])

    def test_registry_fixture(self):
        status,out=self.invoke(["mcp-intake",str(ROOT/"examples/mcp_registry_page.json")])
        self.assertEqual(status,0)
        self.assertEqual(out["page_size"],2)
        self.assertEqual(out["approval"],"MANUAL_SECURITY_REVIEW_REQUIRED")

    def test_review_denies_install(self):
        status,out=self.invoke(["mcp-assess",str(ROOT/"examples/mcp_candidate_review.json")])
        self.assertEqual(status,0)
        self.assertFalse(out["install_allowed"])
        self.assertEqual(out["score_0_100"],0)

    def test_schema_plan_never_executes(self):
        status,out=self.invoke(["mcp-tool-plan",str(ROOT/"examples/mcp_tool_plan.json")])
        self.assertEqual(status,0)
        self.assertEqual(out["selected_count"],1)
        self.assertFalse(out["executed"])
        self.assertEqual([x["name"] for x in out["descriptors"]],["read_docs"])

    def test_sources_unverified(self):
        status,out=self.invoke(["mcp-sources"])
        self.assertEqual(status,0)
        self.assertIn("reported_unverified",out["registries"][0]["verification"])
        self.assertTrue(out["no_auto_payments"])
        self.assertEqual(out["zeus_status"],"ON_HOLD_AWAITING_USER_MATERIAL")

    def test_parser_offline_commands(self):
        verbs=("mcp-intake","mcp-assess","mcp-tool-plan","mcp-registry-url","mcp-sources")
        for verb in verbs:
            with self.subTest(verb=verb):
                args=[verb,"x.json"] if verb in ("mcp-intake","mcp-assess","mcp-tool-plan") else [verb]
                self.assertEqual(build_parser().parse_args(args).command,verb)

if __name__=="__main__":
    unittest.main()
