import unittest
from decimal import Decimal
from pathlib import Path
from omega_builder.finops import ModelQuote, RoutingError, SpendMeter, choose_model, rank_models
from omega_builder.protocol_model import explore, initial, invariant, MailboxState, successors
from omega_builder.catalog import catalog_index, load_catalog


def local(name="edge", quality=0.90, healthy=True, cost="0.04"):
    return ModelQuote(name, "edge", quality, 120, Decimal("0"), Decimal("0"),
                      infrastructure_usd_per_call=Decimal(cost), healthy=healthy)


def external(name="frontier", healthy=True):
    return ModelQuote(name, "frontier", .98, 80, Decimal("2"), Decimal("8"), healthy=healthy)


class MarsCatalogueTests(unittest.TestCase):
    def test_mars_variants_are_distinct_and_unconnected(self):
        f = catalog_index("frameworks", "frameworks")
        mars = load_catalog("mars_variants")
        self.assertEqual(len(mars["variants"]), 3)
        self.assertEqual(mars["resolution"], "ambiguous_requires_user_variant_choice")
        for variant in mars["variants"]:
            item = f[variant["framework_id"]]
            self.assertEqual(item["integration"], "not_connected")
            self.assertEqual(item["status"], "candidate_unverified")

    def test_zeus_still_not_created(self):
        root = Path(__file__).resolve().parents[1]
        self.assertFalse(list(root.rglob("AGENT.md")))
        zeus = load_catalog("zeus_contract")
        self.assertEqual(zeus["implementation_status"], "ON_HOLD_AWAITING_USER_MATERIAL")


class FinOpsTests(unittest.TestCase):
    def test_choose_cheapest_compliant_model(self):
        decision = choose_model([external(), local()],
            input_tokens=1000, output_tokens=500, min_quality=.85,
            max_latency_ms=300, budget_usd=Decimal("1"))
        self.assertEqual(decision["selected"], "frontier")
        self.assertIn("edge", decision["eligible_fallbacks"])

    def test_external_outage_falls_back_to_edge(self):
        decision = choose_model([external(healthy=False), local()],
            input_tokens=1000, output_tokens=500, min_quality=.85,
            max_latency_ms=300, budget_usd=Decimal("1"))
        self.assertEqual(decision["selected"], "edge")

    def test_privacy_policy_excludes_external(self):
        decision = choose_model([external(), local()],
            input_tokens=1000, output_tokens=500, min_quality=.85,
            max_latency_ms=300, budget_usd=Decimal("1"), allow_external=False)
        self.assertEqual(decision["selected"], "edge")

    def test_quality_gate_no_bad_fallback(self):
        with self.assertRaises(RoutingError):
            choose_model([external(healthy=False), local(quality=.8)],
                input_tokens=1000, output_tokens=500, min_quality=.95,
                max_latency_ms=300, budget_usd=Decimal("1"))

    def test_budget_gate(self):
        self.assertEqual(rank_models([local(cost="0.04")],
            input_tokens=100, output_tokens=100, min_quality=.8,
            max_latency_ms=300, budget_usd=Decimal("0.02")), [])

    def test_no_negative_tokens(self):
        with self.assertRaises(RoutingError):
            local().forecast(-1, 10)

    def test_duplicate_quote_rejected(self):
        with self.assertRaises(RoutingError):
            rank_models([local(), local()], input_tokens=0, output_tokens=0,
                min_quality=.8, max_latency_ms=300, budget_usd=Decimal("1"))

    def test_usage_meter_and_duplicate(self):
        ledger = SpendMeter(Decimal("0.10"))
        self.assertEqual(ledger.record(local(), input_tokens=200,
                         output_tokens=100, request_id="q1"), Decimal("0.04"))
        with self.assertRaises(RoutingError):
            ledger.record(local(), input_tokens=2, output_tokens=2, request_id="q1")
        with self.assertRaises(RoutingError):
            ledger.record(local(cost="0.08"), input_tokens=2,
                          output_tokens=2, request_id="q2")
        self.assertEqual(ledger.spent_usd, Decimal("0.04"))


class FormalModelTests(unittest.TestCase):
    def test_explore_two_tasks_two_workers(self):
        report = explore(2, 2)
        self.assertGreaterEqual(report["states_checked"], 5)
        self.assertEqual(report["terminal_states"], 1)
        self.assertEqual(report["violations"], 0)

    def test_no_double_booking(self):
        state = MailboxState(("leased","leased"), (0,0))
        self.assertFalse(invariant(state, 2))

    def test_single_worker_progress(self):
        report = explore(2, 1)
        self.assertGreater(report["transitions_checked"], 0)

    def test_invalid_model_bounds(self):
        with self.assertRaises(ValueError):
            explore(0, 2)

    def test_terminal_is_legal(self):
        self.assertEqual(successors(MailboxState(("done",),(-1,)), 1), ())


if __name__ == "__main__":
    unittest.main()
