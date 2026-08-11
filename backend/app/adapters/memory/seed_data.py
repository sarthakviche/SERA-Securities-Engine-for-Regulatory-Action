"""Fixture data for local/demo/test runs of the impact_mapping / sop_generation /
evidence_implementation_plan slice, standing in for a real tenant until a
teammate wires up Postgres.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.adapters.memory.store import (
    Department,
    InMemoryOrgStore,
    ObligationRow,
    OrgSOP,
    OrgSOPChunk,
    OrgSystem,
    Tables,
)

ORGANIZATION_ID = UUID("00000000-0000-0000-0000-000000000001")

DEPT_COMPLIANCE = uuid4()
DEPT_IT = uuid4()
DEPT_OPERATIONS = uuid4()

SYS_CRM = uuid4()
SYS_MOBILE_APP = uuid4()

SOP_KYC = uuid4()

OBLIGATION_REVERIFICATION = uuid4()
OBLIGATION_AUDIT_LOG = uuid4()

WORKFLOW_ID = uuid4()
DOCUMENT_ID = uuid4()


def build_store() -> InMemoryOrgStore:
    tables = Tables(
        departments=[
            Department(id=DEPT_COMPLIANCE, organization_id=ORGANIZATION_ID, name="Compliance"),
            Department(id=DEPT_IT, organization_id=ORGANIZATION_ID, name="IT Services"),
            Department(id=DEPT_OPERATIONS, organization_id=ORGANIZATION_ID, name="Operations"),
        ],
        systems=[
            OrgSystem(id=SYS_CRM, organization_id=ORGANIZATION_ID, name="CRM Client Records", owner_department_id=DEPT_IT),
            OrgSystem(id=SYS_MOBILE_APP, organization_id=ORGANIZATION_ID, name="Mobile Client App", owner_department_id=DEPT_IT),
        ],
        sops=[
            OrgSOP(
                id=SOP_KYC,
                organization_id=ORGANIZATION_ID,
                department_id=DEPT_OPERATIONS,
                title="Client Mobile Verification SOP",
                content=(
                    "Section 4.2: Registered mobile numbers shall be periodically "
                    "re-verified every 24 months via SMS OTP."
                ),
                version=2,
            )
        ],
        sop_chunks=[
            OrgSOPChunk(
                id=uuid4(),
                sop_id=SOP_KYC,
                organization_id=ORGANIZATION_ID,
                chunk_text=(
                    "Section 4.2: Registered mobile numbers shall be periodically "
                    "re-verified every 24 months via SMS OTP."
                ),
            ),
        ],
        obligations=[
            ObligationRow(
                id=OBLIGATION_REVERIFICATION,
                workflow_id=WORKFLOW_ID,
                organization_id=ORGANIZATION_ID,
                description=(
                    "Verify registered client mobile numbers every 12 months using an "
                    "authenticated mechanism and retain verification logs."
                ),
                frequency="annual",
                evidence_type="verification_log",
                status="proposed",
            ),
            ObligationRow(
                id=OBLIGATION_AUDIT_LOG,
                workflow_id=WORKFLOW_ID,
                organization_id=ORGANIZATION_ID,
                description="Retain OTP verification audit logs for the re-verification obligation.",
                frequency="one_time",
                evidence_type="audit_log_export",
                status="proposed",
            ),
        ],
    )
    return InMemoryOrgStore(tables)


def build_seed_swd_dict() -> dict:
    """A minimal but plausible `agent_outputs`/`human_approvals` block for the
    3 upstream agents + gate_1, as if that part of the pipeline already ran.
    Matches the shapes impact_mapping_agent's REQUIRED_FIELDS expects — see
    ai/graph/projections.py.
    """

    return {
        "document_metadata": {
            "title": "SEBI/HO/MIRSD/2026/104 — Periodic Re-verification of Registered Client Mobile Numbers",
            "circular_reference": "SEBI/HO/MIRSD/2026/104",
            "source": "SEBI",
        },
        "agent_outputs": {
            "obligation_extraction_agent": {
                "obligations": [
                    {
                        "obligation_id": str(OBLIGATION_REVERIFICATION),
                        "description": (
                            "Verify registered client mobile numbers every 12 months using an "
                            "authenticated mechanism and retain verification logs."
                        ),
                        "frequency": "annual",
                        "evidence_type_hint": "verification_log",
                    },
                    {
                        "obligation_id": str(OBLIGATION_AUDIT_LOG),
                        "description": "Retain OTP verification audit logs for the re-verification obligation.",
                        "frequency": "one_time",
                        "evidence_type_hint": "audit_log_export",
                    },
                ]
            },
            "change_analysis_agent": {
                "summary": "Re-verification interval reduced from 24 months to 12 months; adds mandatory audit logging.",
            },
            "ambiguity_detection_agent": {
                "resolved_clarifications": [],
            },
        },
        "human_approvals": {
            "gate_1": {
                "decision": "approved",
                "approved_by": str(uuid4()),
                "approved_at": "2026-07-14T10:15:00Z",
                "comment": None,
            }
        },
        "execution_history": [],
        "agent_tasks": [],
    }
