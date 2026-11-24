"""Tests for the SERA deterministic engine (no DB, no network)."""
from datetime import date

from app.engine import analyzer
from app.engine.audit import GENESIS, compute_hash
from app.engine.text import parse_text

CIRCULAR = """CIRCULAR
HO/38/11/(1)2026-MIRSD-POD/I/7656/2026 March 23, 2026
To,
All recognized Stock Exchanges
All Depositories
Madam / Sir,
Sub: Relaxations in reporting requirements for Stock Brokers
1. In terms of para 15.3 of Master Circular, all demat accounts maintained by brokers should be appropriately tagged.
2. Stock brokers shall report only those bank accounts to the stock exchanges which are used for broking activities.
3. Closure of any of the reported bank accounts shall be communicated to the stock exchanges within seven working days of its closure.
4. The provisions at para 2 shall not be applicable to stock brokers which are also primary dealers.
5. Any non-compliance shall attract penal action as per the provisions of stock exchanges.
6. The provisions of this circular shall come into force with effect from April 17, 2026.
7. This circular is issued in exercise of powers conferred under Section 11(1) of the SEBI Act, 1992.
Yours faithfully,
"""

ORG = {"entity_types": ["stock_broker"]}


def _run(org=ORG):
    circ = parse_text(CIRCULAR)
    return circ, analyzer.build_obligations(circ, org, today=date(2026, 4, 1))


def test_header_parsing():
    circ = parse_text(CIRCULAR)
    assert circ.date == "2026-03-23"
    assert "All Depositories" in circ.addressees
    assert circ.subject.startswith("Relaxations")
    assert [p.ref for p in circ.paragraphs][:3] == ["Para 1", "Para 2", "Para 3"]


def test_every_obligation_quotes_its_source_verbatim():
    circ, res = _run()
    by_ref = {p.ref: p.text for p in circ.paragraphs}
    assert res["obligations"]
    for ob in res["obligations"]:
        assert ob["source_text"] in by_ref[ob["paragraph_ref"]]


def test_boilerplate_and_penalty_are_not_obligations():
    _, res = _run()
    refs = {o["paragraph_ref"] for o in res["obligations"]}
    assert "Para 7" not in refs  # powers conferred
    assert "Para 5" not in refs  # penalty clause raises risk instead
    assert res["penalty_clauses"]


def test_exemption_and_effective_date():
    _, res = _run()
    kinds = {o["paragraph_ref"]: o["kind"] for o in res["obligations"]}
    assert kinds["Para 4"] == "exemption"
    assert res["effective_date"] == "2026-04-17"


def test_event_driven_sla_has_no_fixed_due_date():
    _, res = _run()
    ob = next(o for o in res["obligations"] if o["paragraph_ref"] == "Para 3")
    assert ob["due_date"] is None
    assert ob["frequency"] == "event-driven SLA"


def test_applicability_follows_org_profile():
    _, res = _run({"entity_types": ["mutual_fund"]})
    para2 = next(o for o in res["obligations"] if o["paragraph_ref"] == "Para 2")
    assert para2["applicable"] is False
    _, res = _run()
    para2 = next(o for o in res["obligations"] if o["paragraph_ref"] == "Para 2")
    assert para2["applicable"] is True


def test_ambiguity_flagged():
    _, res = _run()
    tagged = next(o for o in res["obligations"] if "tagged" in o["source_text"])
    assert any(a["type"] == "Undefined standard" for a in tagged["ambiguity"])


def test_llm_hallucination_guard_drops_unverifiable_quotes():
    circ = parse_text(CIRCULAR)
    fake = [{"paragraph_ref": "Para 2", "source_quote": "Brokers must file a daily crypto report.", "kind": "obligation",
             "title": "Fake", "action": "Fake", "category": "Reporting & Disclosure"}]
    res = analyzer.build_obligations(circ, ORG, today=date(2026, 4, 1), llm_proposals=fake)
    assert all("crypto" not in o["source_text"] for o in res["obligations"])


def test_plan_and_impact():
    _, res = _run()
    obs = res["obligations"]
    for i, o in enumerate(obs):
        o["code"] = f"OB-T-{i}"
    impact = analyzer.impact_map(obs, {"departments": ["Compliance", "Operations", "Legal"], "systems": []})
    assert impact["mappings"]
    plan = analyzer.implementation_plan(obs, impact, date(2026, 4, 1))
    assert {t["phase"] for t in plan["tasks"]} >= {"Assess", "Validate"}


def test_audit_hash_chain_detects_tampering():
    from datetime import datetime, timezone

    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    h1 = compute_hash(GENESIS, workflow_id=None, kind="SYSTEM", title="a", detail=None, actor="x", payload=None, created_at=t)
    h1b = compute_hash(GENESIS, workflow_id=None, kind="SYSTEM", title="A", detail=None, actor="x", payload=None, created_at=t)
    assert h1 != h1b and len(h1) == 64
