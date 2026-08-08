"""Audit Repository — TRD §3 names `modules/audit/`; added here (repository
layer only), read-only for now. The actual append happens transactionally
via `InMemoryExecutionTransaction.insert_audit_log` (adapters/memory/store.py)
during `execution_handoff`.

Note for the real implementation: TRD §4.2 revokes UPDATE/DELETE on
`audit_log` for the app DB role — append-only, no exceptions.
"""

from app.modules.audit.repository_protocol import AuditRepository
from app.modules.audit.repository_memory import InMemoryAuditRepository

__all__ = [
    "AuditRepository",
    "InMemoryAuditRepository",
]
