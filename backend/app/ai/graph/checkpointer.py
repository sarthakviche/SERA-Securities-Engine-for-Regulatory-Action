"""LangGraph checkpointer wiring (TRD §8.4).

Real deployment: `langgraph-checkpoint-postgres`'s `AsyncPostgresSaver`,
pointed at `DATABASE_URL` (same Postgres instance as everything else, per
TRD §1 "Postgres is the single source of truth"). Until a teammate wires
that up, this slice uses LangGraph's own built-in `MemorySaver` — a
one-line swap when the real one lands, not a hand-rolled fake like the rest
of this slice's adapters.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer() -> MemorySaver:
    return MemorySaver()
