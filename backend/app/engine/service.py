"""SERA workflow orchestrator (Postgres-backed state machine).

created -> in_analysis -> pending_approval_1 (Gate 1: interpretation sign-off)
        -> planning -> pending_approval_2 (Gate 2: plan sign-off)
        -> executing -> compliant
Side states: needs_ocr (scanned PDF), failed, changes_requested.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.engine import analyzer, audit, llm
from app.engine import taxonomy as tx
from app.engine.text import parse_pdf
from app.models import Obligation, OrgProfile, RegulatoryDocument, Task, WorkflowDocument

logger = logging.getLogger("sera.engine")

ORG_ID = uuid.UUID(settings.ORG_ID_DEFAULT)
EVIDENCE_DIR = settings.DATA_DIR / "evidence"
UPLOAD_DIR = settings.DOWNLOADS_DIR
_running: set[uuid.UUID] = set()

DEFAULT_ORG = {
    "name": "Arthavault Securities Pvt. Ltd.",
    "entity_types": ["stock_broker", "depository_participant", "investment_adviser", "research_analyst"],
    "departments": tx.DEFAULT_DEPARTMENTS,
    "systems": tx.DEFAULT_SYSTEMS,
    "officer_name": "Compliance Officer",
}


# ── org profile ────────────────────────────────────────────────────────────
async def get_org(db: AsyncSession) -> OrgProfile:
    org = await db.get(OrgProfile, 1)
    if org is None:
        org = OrgProfile(id=1, onboarded=False, **DEFAULT_ORG)
        db.add(org)
        await db.flush()
    return org


def org_dict(org: OrgProfile) -> dict[str, Any]:
    return {"name": org.name, "entity_types": org.entity_types, "departments": org.departments,
            "systems": org.systems, "officer_name": org.officer_name, "onboarded": org.onboarded}


# ── notifications ──────────────────────────────────────────────────────────
async def notify(db: AsyncSession, event_type: str, title: str, body: str, workflow_id: uuid.UUID | None) -> None:
    try:
        from app.core.notification_event_publisher import DEFAULT_USER_ID, broadcast_to_user
        from app.modules.notifications.service import notification_service

        n = await notification_service.create(
            db, user_id=DEFAULT_USER_ID, event_type=event_type, title=title, body=body,
            resource_type="workflow" if workflow_id else None, resource_id=workflow_id,
            idempotency_key=f"{event_type}:{workflow_id}:{uuid.uuid4()}",
        )
        if n is not None:
            broadcast_to_user(DEFAULT_USER_ID, {
                "id": str(n.id), "event_type": event_type, "title": title, "body": body,
                "resource_type": n.resource_type, "resource_id": str(workflow_id) if workflow_id else None,
                "is_read": False, "created_at": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:  # noqa: BLE001 - notifications must never break the workflow
        logger.warning("notification failed: %s", exc)


# ── documents ──────────────────────────────────────────────────────────────
async def register_document(
    db: AsyncSession, *, pdf_path: Path | None, title: str | None = None, circular_number: str | None = None,
    issue_date: str | None = None, category: str | None = None, pdf_url: str | None = None,
    origin: str = "scraped", source: str = "SEBI", actor: str = "SERA Monitor",
) -> tuple[RegulatoryDocument, WorkflowDocument, bool]:
    """Idempotent: returns (doc, workflow, created)."""
    key = circular_number or (pdf_path.stem if pdf_path else None) or str(uuid.uuid4())
    doc = (await db.execute(select(RegulatoryDocument).where(RegulatoryDocument.circular_number == key))).scalar_one_or_none()
    created = False
    if doc is None:
        doc = RegulatoryDocument(
            id=uuid.uuid5(uuid.NAMESPACE_URL, key), circular_number=key, title=title or key, issue_date=issue_date,
            category=category, file_ref=pdf_url, pdf_url=pdf_url, local_path=str(pdf_path) if pdf_path else None,
            origin=origin, source=source,
        )
        db.add(doc)
        await db.flush()
        created = True
    elif pdf_path and not doc.local_path:
        doc.local_path = str(pdf_path)
    wf = (await db.execute(select(WorkflowDocument).where(WorkflowDocument.document_id == doc.id))).scalar_one_or_none()
    if wf is None:
        wf = WorkflowDocument(organization_id=ORG_ID, document_id=doc.id, status="created", current_stage="received",
                              progress=0, swd={"history": []})
        db.add(wf)
        await db.flush()
        await audit.record(db, kind="SYSTEM", title=f"Circular received: {doc.title[:200]}", actor=actor,
                           detail=f"{source} {key} ({origin})", workflow_id=wf.id,
                           payload={"circular": key, "origin": origin})
    return doc, wf, created


async def _set(db: AsyncSession, wf: WorkflowDocument, status: str, stage: str, progress: int, **swd_updates) -> None:
    wf.status, wf.current_stage, wf.progress = status, stage, progress
    swd = dict(wf.swd or {})
    hist = list(swd.get("history", []))
    hist.append({"at": datetime.now(timezone.utc).isoformat(), "status": status, "stage": stage})
    swd["history"] = hist[-50:]
    swd.update(swd_updates)
    wf.swd = swd
    await db.flush()


# ── stage 1: analysis ──────────────────────────────────────────────────────
def start_analysis(workflow_id: uuid.UUID) -> bool:
    if workflow_id in _running:
        return False
    _running.add(workflow_id)
    asyncio.create_task(_analysis_job(workflow_id))
    return True


async def _analysis_job(workflow_id: uuid.UUID) -> None:
    try:
        await run_analysis(workflow_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("analysis failed")
        async with AsyncSessionLocal() as db:
            wf = await db.get(WorkflowDocument, workflow_id)
            if wf:
                await _set(db, wf, "failed", "analysis_failed", wf.progress or 0, error=str(exc))
                await audit.record(db, kind="SYSTEM", title="Analysis failed", detail=str(exc)[:500], workflow_id=workflow_id)
                await db.commit()
    finally:
        _running.discard(workflow_id)


async def run_analysis(workflow_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        wf = await db.get(WorkflowDocument, workflow_id)
        doc = await db.get(RegulatoryDocument, wf.document_id)
        org = org_dict(await get_org(db))
        await _set(db, wf, "in_analysis", "parsing", 10)
        await db.commit()

        if not doc.local_path or not Path(doc.local_path).exists():
            raise FileNotFoundError("No PDF available for this circular - upload it or sync from SEBI.")
        circ = await asyncio.to_thread(parse_pdf, doc.local_path)
        doc.text_hash = circ.text_hash
        if circ.is_scanned:
            await _set(db, wf, "needs_ocr", "needs_ocr", 15,
                       analysis={"summary": "This PDF is a scanned image with no text layer. SERA does not guess: "
                                            "upload a text PDF or run OCR before analysis.", "obligations": 0})
            await audit.record(db, kind="AGENT", title="Text extraction blocked - scanned PDF",
                               detail="No machine-readable text found; analysis halted (fail-closed).", workflow_id=wf.id)
            await notify(db, "workflow.needs_review", "Scanned circular needs OCR", doc.title[:200], wf.id)
            await db.commit()
            return
        if circ.subject and (doc.title == doc.circular_number or doc.title.startswith("Document ")):
            doc.title = circ.subject
        if circ.date and not doc.issue_date:
            doc.issue_date = circ.date
        await _set(db, wf, "in_analysis", "extracting_obligations", 35)
        await db.commit()

        proposals, provider = await llm.propose_obligations(circ)
        await _set(db, wf, "in_analysis", "verifying_citations", 60)
        await db.commit()

        result = analyzer.build_obligations(circ, org, llm_proposals=proposals)
        series = _series(circ.circular_number or doc.circular_number)
        await db.execute(delete(Task).where(Task.workflow_id == wf.id))
        await db.execute(delete(Obligation).where(Obligation.workflow_id == wf.id))
        for ob in result["obligations"]:
            ob["code"] = f"OB-{series}-{ob['seq']:02d}"
            db.add(Obligation(
                workflow_id=wf.id, code=ob["code"], title=ob["title"][:500], description=ob["action"],
                category=ob["category"], frequency=ob["frequency"], evidence_type=ob["evidence"][:255],
                status="pending", confidence_score=ob["confidence"], clause_ref=ob["paragraph_ref"],
                source_text=ob["source_text"], page_number=ob["page"], deadline=(ob["deadline_text"] or "")[:120] or None,
                due_date=date.fromisoformat(ob["due_date"]) if ob["due_date"] else None, risk=ob["risk"],
                applicable=ob["applicable"], applicability_reason=ob["applicability_reason"],
                ambiguity=ob["ambiguity"], excluded=not ob["applicable"],
            ))
        doc.summary = result["summary"]
        doc.risk = result["risk"]
        doc.analysis_meta = {"provider": provider, "paragraphs": len(circ.paragraphs), "pages": circ.page_count,
                             "addressees": result["addressees"], "effective_date": result["effective_date"],
                             "penalty_clauses": result["penalty_clauses"],
                             "llm_proposals": len(proposals) if proposals else 0}
        applicable = [o for o in result["obligations"] if o["applicable"]]
        amb = sum(len(o["ambiguity"]) for o in applicable)
        await _set(db, wf, "pending_approval_1", "gate_1", 70, analysis={
            "summary": result["summary"], "provider": provider, "obligations": len(result["obligations"]),
            "applicable": len(applicable), "ambiguities": amb, "risk": result["risk"],
            "paragraphs": [{"ref": p.ref, "page": p.page, "text": p.text} for p in circ.paragraphs],
            "circular_number": circ.circular_number, "circular_date": circ.date, "addressees": circ.addressees,
        })
        await audit.record(
            db, kind="AGENT", title=f"Analysis complete: {len(applicable)} applicable obligation(s)", workflow_id=wf.id,
            actor=f"SERA Engine ({provider})",
            detail=f"{len(result['obligations'])} requirements found across {len(circ.paragraphs)} paragraphs; "
                   f"{amb} ambiguity flag(s). Every obligation cites its source paragraph.",
            payload={"text_hash": circ.text_hash, "codes": [o["code"] for o in result["obligations"]]},
        )
        await notify(db, "workflow.gate_pending", "Interpretation awaiting approval (Gate 1)",
                     f"{doc.title[:150]} - {len(applicable)} applicable obligation(s)", wf.id)
        await db.commit()


def _series(circular_number: str | None) -> str:
    if not circular_number:
        return "GEN"
    m = re.search(r"\b(MIRSD|MRD|CFD|IMD|DDHS|AFD|MIRSD-POD\d?|ITD|DEPA|MSD)\b", circular_number)
    num = re.findall(r"(\d{3,6})", circular_number)
    tag = (m.group(1).split("-")[0] if m else "SEBI")
    return f"{tag}-{num[-2] if len(num) >= 2 else (num[-1] if num else '0')}"


# ── stage 2: planning ──────────────────────────────────────────────────────
async def _obligation_dicts(db: AsyncSession, wf_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (await db.execute(select(Obligation).where(Obligation.workflow_id == wf_id).order_by(Obligation.code))).scalars().all()
    return [{
        "id": str(o.id), "code": o.code, "title": o.title, "action": o.description, "category": o.category,
        "source_text": o.source_text or "", "paragraph_ref": o.clause_ref, "risk": o.risk or "MEDIUM",
        "applicable": o.applicable and not o.excluded, "excluded": o.excluded, "deadline_text": o.deadline,
        "due_date": o.due_date.isoformat() if o.due_date else None, "frequency": o.frequency,
        "evidence": o.evidence_type or "", "kind": "exemption" if (o.category == "Exemption") else "obligation",
        "extended_by": "extended per" in (o.deadline or ""),
    } for o in rows]


async def run_planning(db: AsyncSession, wf: WorkflowDocument, feedback: str | None = None) -> None:
    org = org_dict(await get_org(db))
    doc = await db.get(RegulatoryDocument, wf.document_id)
    obs = await _obligation_dicts(db, wf.id)
    impact = analyzer.impact_map(obs, org)
    sops = analyzer.sop_drafts(obs, impact, doc.circular_number)
    plan = analyzer.implementation_plan(obs, impact, date.today())
    by_code = {m["obligation_code"]: m for m in impact["mappings"]}
    for o in (await db.execute(select(Obligation).where(Obligation.workflow_id == wf.id))).scalars():
        m = by_code.get(o.code)
        if m:
            o.department = m["departments"][0]["department"]
            o.owner = f"{o.department} Head"
            o.impact = m
    revision = int((wf.swd or {}).get("plan_revision", 0)) + (1 if feedback else 0)
    if feedback:
        plan["feedback_applied"] = feedback
    await _set(db, wf, "pending_approval_2", "gate_2", 85, impact=impact, sops=sops, plan=plan, plan_revision=revision)
    await audit.record(db, kind="AGENT", title=f"Impact map, SOP drafts & plan ready ({len(plan['tasks'])} tasks)",
                       workflow_id=wf.id, detail=(f"Revision {revision} after feedback: {feedback}" if feedback else
                                                  f"{len(impact['mappings'])} obligation(s) mapped; "
                                                  f"{len(impact['needs_review'])} mapping(s) need human review."))
    await notify(db, "workflow.gate_pending", "Implementation plan awaiting approval (Gate 2)", doc.title[:200], wf.id)


# ── gates ──────────────────────────────────────────────────────────────────
async def gate_decision(db: AsyncSession, wf: WorkflowDocument, gate: str, decision: str, comment: str | None,
                        actor: str, excluded_codes: list[str] | None = None) -> None:
    swd = dict(wf.swd or {})
    approvals = dict(swd.get("approvals", {}))
    approvals[gate] = {"decision": decision, "comment": comment, "by": actor,
                       "at": datetime.now(timezone.utc).isoformat()}
    wf.swd = {**swd, "approvals": approvals}
    await audit.record(db, kind="APPROVAL", title=f"{'Gate 1 (interpretation)' if gate == 'gate_1' else 'Gate 2 (plan)'} "
                                                  f"{decision}", actor=actor, detail=comment, workflow_id=wf.id,
                       payload={"gate": gate, "decision": decision, "excluded": excluded_codes or []})
    if gate == "gate_1":
        if wf.status != "pending_approval_1":
            raise ValueError(f"Gate 1 not pending (status={wf.status})")
        if decision == "approved":
            for o in (await db.execute(select(Obligation).where(Obligation.workflow_id == wf.id))).scalars():
                if excluded_codes is not None:
                    o.excluded = o.code in excluded_codes
                o.status = "waived" if o.excluded else "active"
            await _set(db, wf, "planning", "impact_mapping", 75)
            await run_planning(db, wf)
        else:
            await _set(db, wf, "changes_requested", "gate_1_rejected", 60)
    elif gate == "gate_2":
        if wf.status != "pending_approval_2":
            raise ValueError(f"Gate 2 not pending (status={wf.status})")
        if decision == "approved":
            await _materialize_tasks(db, wf)
            await _set(db, wf, "executing", "implementation", 90)
            await notify(db, "task.created", "Implementation started", "Tasks were assigned to departments.", wf.id)
        else:
            await run_planning(db, wf, feedback=comment or "Revise plan")


async def _materialize_tasks(db: AsyncSession, wf: WorkflowDocument) -> None:
    plan = (wf.swd or {}).get("plan", {})
    obs = {o.code: o for o in (await db.execute(select(Obligation).where(Obligation.workflow_id == wf.id))).scalars()}
    await db.execute(delete(Task).where(Task.workflow_id == wf.id))
    for t in plan.get("tasks", []):
        ob = obs.get(t["obligation_code"])
        db.add(Task(workflow_id=wf.id, obligation_id=ob.id if ob else None, title=t["title"][:500],
                    description=t["description"], status="Pending", priority=t["priority"],
                    due_date=date.fromisoformat(t["due_date"]), evidence_requirement=t.get("evidence_requirement"),
                    department=t["department"], assignee=f"{t['department']} Head", phase=t["phase"]))
    await db.flush()


# ── execution ──────────────────────────────────────────────────────────────
async def update_task(db: AsyncSession, task: Task, *, status: str | None, actor: str, note: str | None = None,
                      file_name: str | None = None, file_bytes: bytes | None = None) -> None:
    if file_bytes is not None:
        digest = hashlib.sha256(file_bytes).hexdigest()
        folder = EVIDENCE_DIR / str(task.id)
        folder.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w.\- ]", "_", file_name or "evidence.bin")[:120]
        (folder / safe).write_bytes(file_bytes)
        files = list(task.evidence_files or [])
        files.append({"name": safe, "size": len(file_bytes), "sha256": digest,
                      "uploaded_at": datetime.now(timezone.utc).isoformat(), "by": actor})
        task.evidence_files = files
        await audit.record(db, kind="EVIDENCE", title=f"Evidence uploaded: {safe}", actor=actor,
                           detail=f"Task: {task.title[:200]}", workflow_id=task.workflow_id,
                           payload={"task_id": str(task.id), "file": safe, "sha256": digest, "size": len(file_bytes)})
    if note:
        task.evidence_note = note
    if status and status != task.status:
        if status == "Completed" and task.evidence_requirement and not (task.evidence_files or task.evidence_note):
            raise ValueError("Evidence is required before this task can be completed.")
        prev = task.status
        task.status = status
        task.completed_at = datetime.now(timezone.utc) if status == "Completed" else None
        await audit.record(db, kind="REQUEST" if status != "Completed" else "EVIDENCE",
                           title=f"Task {status.lower()}: {task.title[:180]}", actor=actor,
                           detail=f"{prev} -> {status}" + (f" | {note}" if note else ""), workflow_id=task.workflow_id)
    await db.flush()
    await _rollup(db, task.workflow_id)


async def _rollup(db: AsyncSession, wf_id: uuid.UUID) -> None:
    tasks = (await db.execute(select(Task).where(Task.workflow_id == wf_id))).scalars().all()
    if not tasks:
        return
    by_ob: dict[uuid.UUID, list[Task]] = {}
    for t in tasks:
        if t.obligation_id:
            by_ob.setdefault(t.obligation_id, []).append(t)
    for ob_id, ts in by_ob.items():
        ob = await db.get(Obligation, ob_id)
        if ob and not ob.excluded:
            ob.status = "completed" if all(t.status == "Completed" for t in ts) else "active"
    wf = await db.get(WorkflowDocument, wf_id)
    done = sum(t.status == "Completed" for t in tasks)
    if wf.status in ("executing", "compliant"):
        if done == len(tasks):
            if wf.status != "compliant":
                await _set(db, wf, "compliant", "monitoring", 100)
                doc = await db.get(RegulatoryDocument, wf.document_id)
                await audit.record(db, kind="APPROVAL", title="Circular fully implemented - compliant",
                                   detail=doc.title[:250], workflow_id=wf_id, actor="SERA Engine")
                await notify(db, "workflow.completed", "Circular compliant", doc.title[:200], wf_id)
        else:
            wf.progress = 90 + int(10 * done / len(tasks)) if done else 90
            if wf.status == "compliant":
                await _set(db, wf, "executing", "implementation", wf.progress)


async def mark_overdue(db: AsyncSession) -> int:
    today = date.today()
    rows = (await db.execute(select(Task).where(Task.status.in_(["Pending", "In Progress"]), Task.due_date < today))).scalars().all()
    for t in rows:
        t.status = "Overdue"
    return len(rows)


# ── seed / sync ────────────────────────────────────────────────────────────
async def seed_local_pdfs(db: AsyncSession) -> int:
    """Register every PDF in downloads/ (and legacy documents.json metadata) as a circular."""
    import json

    meta: dict[str, dict] = {}
    try:
        for d in json.loads(settings.DOCUMENTS_FILE.read_text(encoding="utf-8")):
            meta[d["document_id"]] = d
    except Exception:  # noqa: BLE001
        pass
    n = 0
    for pdf in sorted(settings.DOWNLOADS_DIR.glob("*.pdf")):
        m = meta.get(pdf.stem, {})
        title = m.get("title")
        issue = m.get("publication_date")
        if not title:
            try:
                c = await asyncio.to_thread(parse_pdf, pdf)
                title, issue = c.subject, c.date
            except Exception:  # noqa: BLE001
                pass
        _, _, created = await register_document(
            db, pdf_path=pdf, title=title or pdf.stem, circular_number=pdf.stem, issue_date=issue,
            category=m.get("category", "Circulars"), pdf_url=m.get("pdf_url"), origin="seed")
        n += int(created)
    return n


async def sync_sebi(db: AsyncSession) -> dict[str, Any]:
    """Run the existing scraper+downloader, then register anything new."""
    from app.workers import monitor

    report = await asyncio.to_thread(monitor.run_monitoring_cycle)
    added = 0
    for d in report.downloaded_documents:
        if d.local_pdf_path and Path(d.local_pdf_path).exists():
            _, _, created = await register_document(
                db, pdf_path=Path(d.local_pdf_path), title=d.title, circular_number=d.document_id,
                issue_date=d.publication_date, category=d.type, pdf_url=d.pdf_url, origin="scraped")
            added += int(created)
    return {"new": len(report.new_documents), "registered": added, "errors": report.errors}


async def save_upload(db: AsyncSession, filename: str, data: bytes, source: str, actor: str):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^\w\-]", "_", Path(filename).stem)[:80] or "circular"
    digest = hashlib.sha256(data).hexdigest()[:10]
    path = UPLOAD_DIR / f"UPLOAD-{stem}-{digest}.pdf"
    path.write_bytes(data)
    c = await asyncio.to_thread(parse_pdf, path)
    return await register_document(db, pdf_path=path, title=c.subject or Path(filename).stem,
                                   circular_number=c.circular_number or path.stem, issue_date=c.date,
                                   category="Uploaded", origin="upload", source=source, actor=actor)


async def counts(db: AsyncSession) -> dict[str, int]:
    rows = (await db.execute(select(WorkflowDocument.status, func.count()).group_by(WorkflowDocument.status))).all()
    return {s: c for s, c in rows}


