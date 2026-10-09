"""Bounded reference state exploration for task leasing; NOT a proof of network safety."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class MailboxState:
    stages: tuple[str, ...]
    owners: tuple[int, ...]  # -1 means no owner


def initial(task_count: int) -> MailboxState:
    if task_count < 1:
        raise ValueError("At least one task")
    return MailboxState(("queued",) * task_count, (-1,) * task_count)


def invariant(state: MailboxState, workers: int) -> bool:
    if workers < 1 or len(state.stages) != len(state.owners):
        return False
    live_owners = []
    for stage, owner in zip(state.stages, state.owners):
        if stage not in ("queued", "leased", "done"):
            return False
        if (stage == "leased") != (owner >= 0):
            return False
        if owner >= workers:
            return False
        if owner >= 0:
            live_owners.append(owner)
    return len(live_owners) == len(set(live_owners))


def successors(state: MailboxState, workers: int) -> tuple[MailboxState, ...]:
    out = []
    for index, stage in enumerate(state.stages):
        choices = []
        if stage == "queued":
            busy = set(state.owners) - {-1}
            choices = [("leased", w) for w in range(workers) if w not in busy]
        elif stage == "leased":
            choices = [("queued", -1), ("done", -1)]
        for next_stage, next_owner in choices:
            stages = list(state.stages)
            owners = list(state.owners)
            stages[index] = next_stage
            owners[index] = next_owner
            out.append(MailboxState(tuple(stages), tuple(owners)))
    return tuple(out)


def explore(task_count: int = 2, workers: int = 2, limit: int = 100_000) -> dict[str, int]:
    if workers < 1 or limit < 1 or task_count < 1:
        raise ValueError("Invalid model bounds")
    seed = initial(task_count)
    visited = {seed}
    queue = deque([seed])
    edges = 0
    terminal = 0
    while queue:
        state = queue.popleft()
        if not invariant(state, workers):
            raise AssertionError(f"Mailbox invariant violation: {state}")
        next_states = successors(state, workers)
        if not next_states:
            if any(stage != "done" for stage in state.stages):
                raise AssertionError(f"Nonterminal deadlock: {state}")
            terminal += 1
        for next_state in next_states:
            edges += 1
            if next_state not in visited:
                if len(visited) >= limit:
                    raise ValueError("State exploration budget exhausted")
                visited.add(next_state)
                queue.append(next_state)
    return {"states_checked": len(visited), "transitions_checked": edges,
            "terminal_states": terminal, "violations": 0}
