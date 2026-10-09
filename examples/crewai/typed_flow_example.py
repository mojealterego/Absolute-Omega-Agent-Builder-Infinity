"""Opt-in CrewAI SDK Flow example. Not an autonomous Agent or Zeus.

Requires a separately installed, version-pinned compatible CrewAI/Pydantic.
No LLM, network calls, tools, memory, persistence or side effects on import.
"""
from typing import Literal
from crewai.flow.flow import Flow, start, listen, router
from pydantic import BaseModel, Field


class ControlledState(BaseModel):
    text: str = Field(default="", max_length=2048)
    approved: bool = False
    outcome: Literal["new", "accepted", "rejected"] = "new"


class ControlledReviewFlow(Flow[ControlledState]):
    """Pure local Flow demonstrating typed state + fixed conditional routing."""

    @start()
    def inspect_input(self) -> bool:
        self.state.approved = bool(self.state.text.strip())
        return self.state.approved

    @router(inspect_input)
    def branch(self, accepted: bool) -> str:
        return "allowed" if accepted else "denied"

    @listen("allowed")
    def mark_allowed(self) -> str:
        self.state.outcome = "accepted"
        return self.state.outcome

    @listen("denied")
    def mark_denied(self) -> str:
        self.state.outcome = "rejected"
        return self.state.outcome


def build_example_only() -> ControlledReviewFlow:
    """Construct a Flow but never call kickoff implicitly."""
    return ControlledReviewFlow()
