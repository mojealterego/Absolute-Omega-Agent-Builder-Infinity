"""Offline reference FinOps: honest price/usage accounting and guarded model selection.

No live provider connection. Costs are USD estimates based on user-supplied pricing.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


class RoutingError(ValueError):
    """No provider satisfies constraints, or invalid budget data."""


def usd(value: object) -> Decimal:
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise RoutingError("Invalid currency amount") from exc
    if not number.is_finite() or number < 0:
        raise RoutingError("Cost must be finite and non-negative")
    return number


@dataclass(frozen=True)
class ModelQuote:
    name: str
    backend: str                 # "frontier" or "edge"
    quality_score: float         # supplied, independently validated 0..1
    p95_latency_ms: int          # observed p95, not a promise
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal
    infrastructure_usd_per_call: Decimal = Decimal("0")
    healthy: bool = True

    def validate(self) -> None:
        if not self.name or self.backend not in ("frontier", "edge"):
            raise RoutingError("Model name and backend required")
        if not 0 <= self.quality_score <= 1:
            raise RoutingError("Invalid quality score")
        if not isinstance(self.p95_latency_ms, int) or self.p95_latency_ms <= 0:
            raise RoutingError("Latency must be a positive integer")
        for value in (self.input_usd_per_million, self.output_usd_per_million,
                      self.infrastructure_usd_per_call):
            usd(value)

    def forecast(self, input_tokens: int, output_tokens: int) -> Decimal:
        self.validate()
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            raise RoutingError("Token counts must be integers")
        if input_tokens < 0 or output_tokens < 0:
            raise RoutingError("Token counts cannot be negative")
        return (
            usd(self.input_usd_per_million) * Decimal(input_tokens) / Decimal(1_000_000)
            + usd(self.output_usd_per_million) * Decimal(output_tokens) / Decimal(1_000_000)
            + usd(self.infrastructure_usd_per_call)
        )


def rank_models(
    quotes: Iterable[ModelQuote], *,
    input_tokens: int, output_tokens: int,
    min_quality: float, max_latency_ms: int,
    budget_usd: Decimal, allow_external: bool = True
) -> list[tuple[str, Decimal]]:
    """Return all feasible models ordered by estimated TOTAL cost."""
    if not 0 <= min_quality <= 1 or max_latency_ms <= 0:
        raise RoutingError("Invalid quality or latency policy")
    budget = usd(budget_usd)
    rows = []
    used = set()
    for quote in quotes:
        quote.validate()
        if quote.name in used:
            raise RoutingError("Duplicate model name")
        used.add(quote.name)
        cost = quote.forecast(input_tokens, output_tokens)
        if not quote.healthy or quote.quality_score < min_quality:
            continue
        if quote.p95_latency_ms > max_latency_ms:
            continue
        if not allow_external and quote.backend != "edge":
            continue
        if cost > budget:
            continue
        rows.append((quote.name, cost))
    return sorted(rows, key=lambda row: (row[1], row[0]))


def choose_model(quotes: Iterable[ModelQuote], **policy: object) -> dict[str, object]:
    ranked = rank_models(quotes, **policy)
    if not ranked:
        raise RoutingError("No compliant provider: halt or request human approval")
    return {
        "selected": ranked[0][0],
        "estimated_usd": str(ranked[0][1]),
        "eligible_fallbacks": [name for name, _ in ranked[1:]],
        "verification": "offline_estimate_not_live_API",
    }


class SpendMeter:
    """Offline reconciliation ledger; caller passes observed provider token usage."""

    def __init__(self, budget_usd: Decimal):
        self.budget_usd = usd(budget_usd)
        self.spent_usd = Decimal("0")
        self.usage_events = []

    def record(self, quote: ModelQuote, *, input_tokens: int, output_tokens: int,
               request_id: str) -> Decimal:
        if not request_id or any(e["request_id"] == request_id for e in self.usage_events):
            raise RoutingError("Unique request_id required")
        amount = quote.forecast(input_tokens, output_tokens)
        if self.spent_usd + amount > self.budget_usd:
            raise RoutingError("Spend budget exceeded; fail closed")
        self.spent_usd += amount
        self.usage_events.append({
            "request_id": request_id,
            "model": quote.name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "billed_usd_from_config": str(amount),
            "note": "provider reconciliation required",
        })
        return amount
