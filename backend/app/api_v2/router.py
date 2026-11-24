"""SERA v2 API - the single API the frontend uses."""
from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.engine import audit, llm, service
from app.engine import taxonomy as tx
from app.models import AuditEvent, Obligation, OrgProfile, RegulatoryDocument, Task, WorkflowDocument

router = APIRouter(prefix="/api/v2", tags=["sera-v2"])

STAGE_MAP = {  # backend status -> UI pipeline column
    "created": "RECEIVED", "in_analysis": "ANALYSING", "needs_ocr": "ANALYSING", "failed": "ANALYSING",
    "changes_requested": "ANALYSING", "pending_approval_1": "AWAITING_APPROVAL", "planning": "AWAITING_APPROVAL",
    "pending_approval_2": "AWAITING_APPROVAL", "executing": "IMPLEMENTATION", "compliant": "MONITORING",
}


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── serializers ────────────────────────────────────────────────────────────
def ser_doc(doc: RegulatoryDocument, wf: WorkflowDocument | None, ob_count: int = 0) -> dict[str, Any]:
    swd = (wf.swd or {}) if wf else {}
    return {
        "id": str(doc.id), "workflow_id": str(wf.id) if wf else None, "reference": doc.circular_number,
        "title": doc.title, "summary": doc.summary, "source": doc.source, "issue_date": doc.issue_date,
        "category": doc.category, "risk": doc.risk or "LOW", "origin": doc.origin, "pdf_url": doc.pdf_url,
        "has_pdf": bool(doc.local_path and Path(doc.local_path).exists()),
        "received_at": doc.created_at.isoformat() if doc.created_at else None,
        "status": wf.status if wf else "created", "stage": STAGE_MAP.get(wf.status if wf else "created", "RECEIVED"),
        "current_stage": wf.current_stage if wf else None, "progress": wf.progress if wf else 0,
        "obligation_count": ob_count, "provider": (doc.analysis_meta or {}).get("provider"),
        "error": swd.get("error"),
        "updated_at": wf.updated_at.isoformat() if wf and wf.updated_at else None,
    }


def ser_ob(o: Obligation, doc_ref: str | None = None, tasks: list[Task] | None = None) -> dict[str, Any]:
    ts = tasks or []
    done = sum(t.status == "Completed" for t in ts)
    return {
        "id": str(o.id), "workflow_id": str(o.workflow_id), "code": o.code, "title": o.title,
        "description": o.description, "category": o.category, "clause_ref": o.clause_ref,
        "source_text": o.source_text, "page": o.page_number, "deadline": o.deadline,
        "due_date": o.due_date.isoformat() if o.due_date else None, "frequency": o.frequency,
        "evidence": o.evidence_type, "risk": o.risk or "MEDIUM", "status": o.status,
        "applicable": o.applicable, "excluded": o.excluded, "applicability_reason": o.applicability_reason,
        "ambiguity": o.ambiguity or [], "confidence": o.confidence_score, "department": o.department,
        "owner": o.owner, "impact": o.impact, "circular_ref": doc_ref,
        "progress": int(100 * done / len(ts)) if ts else (100 if o.status == "completed" else 0),
        "task_count": len(ts), "tasks_done": done,
    }


def ser_task(t: Task, ob: Obligation | None = None) -> dict[str, Any]:
    status = t.status
    if status in ("Pending", "In Progress") and t.due_date and t.due_date < date.today():
        status = "Overdue"
    return {
        "id": str(t.id), "workflow_id": str(t.workflow_id), "obligation_id": str(t.obligation_id) if t.obligation_id else None,
        "obligation_code": ob.code if ob else None, "title": t.title, "description": t.description,
        "status": status, "raw_status": t.status, "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else None, "evidence_requirement": t.evidence_requirement,
        "department": t.department, "assignee": t.assignee, "phase": t.phase, "evidence_note": t.evidence_note,
        "evidence_files": t.evidence_files or [], "completed_at": t.completed_at.isoformat() if t.completed_at else None,
    }


def ser_audit(e: AuditEvent) -> dict[str, Any]:
    return {"id": e.id, "workflow_id": str(e.workflow_id) if e.workflow_id else None, "kind": e.kind,
            "title": e.title, "detail": e.detail, "actor": e.actor, "payload": e.payload,
            "hash": e.hash, "prev_hash": e.prev_hash, "at": e.created_at.isoformat()}


# ── meta / org ─────────────────────────────────────────────────────────────
@router.get("/meta")
async def meta(db: AsyncSession = Depends(get_db)):
    return {
        "provider": llm.provider_name(),
        "entity_types": [{"key": k, "label": tx.ENTITY_LABELS[k]} for k in tx.SELECTABLE_ENTITIES],
        "default_departments": tx.DEFAULT_DEPARTMENTS, "default_systems": tx.DEFAULT_SYSTEMS,
        "org": service.org_dict(await service.get_org(db)),
    }


class OrgIn(BaseModel):
    name: str
    entity_types: list[str]
    departments: list[str]
    systems: list[str]
    officer_name: Optional[str] = None


@router.put("/org")
async def update_org(body: OrgIn, db: AsyncSession = Depends(get_db)):
    org: OrgProfile = await service.get_org(db)
    unknown = [e for e in body.entity_types if e not in tx.ENTITY_LABELS]
    if unknown:
        raise HTTPException(422, f"Unknown entity types: {unknown}")
    org.name, org.entity_types, org.departments, org.systems = body.name, body.entity_types, body.departments, body.systems
    org.officer_name, org.onboarded = body.officer_name, True
    await audit.record(db, kind="SYSTEM", title="Organisation profile updated", actor=body.officer_name or "Admin",
                       detail=f"Entity types: {', '.join(tx.ENTITY_LABELS[e] for e in body.entity_types)}")
    return service.org_dict(org)


# ── circulars ──────────────────────────────────────────────────────────────
async def _doc_rows(db: AsyncSession):
    docs = (await db.execute(select(RegulatoryDocument).order_by(RegulatoryDocument.issue_date.desc().nullslast(),
                                                                 RegulatoryDocument.created_at.desc()))).scalars().all()
    wfs = {w.document_id: w for w in (await db.execute(select(WorkflowDocument))).scalars()}
    ob_counts: dict[uuid.UUID, int] = {}
    for o in (await db.execute(select(Obligation.workflow_id).where(Obligation.excluded.is_(False)))).scalars():
        ob_counts[o] = ob_counts.get(o, 0) + 1
    return [ser_doc(d, wfs.get(d.id), ob_counts.get(wfs[d.id].id, 0) if d.id in wfs else 0) for d in docs]


@router.get("/circulars")
async def list_circulars(db: AsyncSession = Depends(get_db)):
    return await _doc_rows(db)


@router.post("/circulars/upload")
async def upload_circular(file: UploadFile = File(...), source: str = Form("SEBI"), actor: str = Form("Compliance Officer"),
                          auto_analyze: bool = Form(True), db: AsyncSession = Depends(get_db)):
    data = await file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(422, "Please upload a PDF file.")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "PDF too large (max 25 MB).")
    doc, wf, created = await service.save_upload(db, file.filename or "circular.pdf", data, source, actor)
    await db.commit()
    if auto_analyze and wf.status in ("created", "failed", "changes_requested"):
        service.start_analysis(wf.id)
    return {"document_id": str(doc.id), "workflow_id": str(wf.id), "created": created}


@router.post("/circulars/sync")
async def sync_circulars(db: AsyncSession = Depends(get_db)):
    try:
        res = await service.sync_sebi(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"SEBI sync failed (network?): {exc}") from exc
    res["seeded"] = await service.seed_local_pdfs(db)
    return res


@router.post("/circulars/{doc_id}/analyze")
async def analyze(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    wf = (await db.execute(select(WorkflowDocument).where(WorkflowDocument.document_id == doc_id))).scalar_one_or_none()
    if wf is None:
        raise HTTPException(404, "Circular not found")
    if wf.status not in ("created", "failed", "changes_requested", "needs_ocr", "pending_approval_1"):
        raise HTTPException(409, f"Analysis cannot be re-run while status is '{wf.status}'.")
    started = service.start_analysis(wf.id)
    return {"workflow_id": str(wf.id), "started": started}


@router.get("/circulars/{doc_id}/pdf")
async def circular_pdf(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(RegulatoryDocument, doc_id)
    if not doc or not doc.local_path or not Path(doc.local_path).exists():
        raise HTTPException(404, "PDF not available")
    return FileResponse(doc.local_path, media_type="application/pdf")


# ── workflows ──────────────────────────────────────────────────────────────
@router.get("/workflows/{wf_id}")
async def workflow_detail(wf_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    wf = await db.get(WorkflowDocument, wf_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    doc = await db.get(RegulatoryDocument, wf.document_id)
    obs = (await db.execute(select(Obligation).where(Obligation.workflow_id == wf_id).order_by(Obligation.code))).scalars().all()
    tasks = (await db.execute(select(Task).where(Task.workflow_id == wf_id).order_by(Task.due_date, Task.title))).scalars().all()
    ob_by_id = {o.id: o for o in obs}
    swd = wf.swd or {}
    return {
        "circular": {**ser_doc(doc, wf, sum(not o.excluded for o in obs)), "analysis_meta": doc.analysis_meta},
        "status": wf.status, "stage": STAGE_MAP.get(wf.status, "RECEIVED"), "current_stage": wf.current_stage,
        "progress": wf.progress, "analysis": swd.get("analysis"), "impact": swd.get("impact"),
        "sops": swd.get("sops"), "plan": swd.get("plan"), "approvals": swd.get("approvals", {}),
        "history": swd.get("history", []), "plan_revision": swd.get("plan_revision", 0),
        "obligations": [ser_ob(o, doc.circular_number, [t for t in tasks if t.obligation_id == o.id]) for o in obs],
        "tasks": [ser_task(t, ob_by_id.get(t.obligation_id)) for t in tasks],
    }


class GateIn(BaseModel):
    decision: str
    comment: Optional[str] = None
    actor: str = "Compliance Officer"
    excluded_codes: Optional[list[str]] = None


@router.post("/workflows/{wf_id}/gate/{gate}")
async def gate(wf_id: uuid.UUID, gate: str, body: GateIn, db: AsyncSession = Depends(get_db)):
    if gate not in ("gate_1", "gate_2") or body.decision not in ("approved", "rejected"):
        raise HTTPException(422, "Invalid gate or decision")
    if body.decision == "rejected" and not (body.comment or "").strip():
        raise HTTPException(422, "A comment is required when rejecting.")
    wf = await db.get(WorkflowDocument, wf_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    try:
        await service.gate_decision(db, wf, gate, body.decision, body.comment, body.actor, body.excluded_codes)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"status": wf.status, "current_stage": wf.current_stage}


# ── obligations ────────────────────────────────────────────────────────────
@router.get("/obligations")
async def list_obligations(include_excluded: bool = False, db: AsyncSession = Depends(get_db)):
    q = select(Obligation).order_by(Obligation.due_date.nullslast(), Obligation.code)
    if not include_excluded:
        q = q.where(Obligation.excluded.is_(False))
    obs = (await db.execute(q)).scalars().all()
    wfs = {w.id: w for w in (await db.execute(select(WorkflowDocument))).scalars()}
    docs = {d.id: d for d in (await db.execute(select(RegulatoryDocument))).scalars()}
    tasks = (await db.execute(select(Task))).scalars().all()
    out = []
    for o in obs:
        wf = wfs.get(o.workflow_id)
        d = docs.get(wf.document_id) if wf else None
        row = ser_ob(o, d.circular_number if d else None, [t for t in tasks if t.obligation_id == o.id])
        row["circular_title"] = d.title if d else None
        row["workflow_status"] = wf.status if wf else None
        out.append(row)
    return out


class ObligationPatch(BaseModel):
    excluded: Optional[bool] = None
    department: Optional[str] = None


@router.patch("/obligations/{ob_id}")
async def patch_obligation(ob_id: uuid.UUID, body: ObligationPatch, db: AsyncSession = Depends(get_db)):
    o = await db.get(Obligation, ob_id)
    if not o:
        raise HTTPException(404, "Obligation not found")
    if body.excluded is not None:
        o.excluded = body.excluded
        await audit.record(db, kind="REQUEST", title=f"{o.code} {'excluded from' if body.excluded else 'included in'} scope",
                           actor="Compliance Officer", workflow_id=o.workflow_id)
    if body.department:
        o.department = body.department
    return ser_ob(o)


# ── tasks ──────────────────────────────────────────────────────────────────
@router.get("/tasks")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    tasks = (await db.execute(select(Task).order_by(Task.due_date, Task.title))).scalars().all()
    obs = {o.id: o for o in (await db.execute(select(Obligation))).scalars()}
    return [ser_task(t, obs.get(t.obligation_id)) for t in tasks]


class TaskPatch(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    actor: str = "Department Owner"


@router.patch("/tasks/{task_id}")
async def patch_task(task_id: uuid.UUID, body: TaskPatch, db: AsyncSession = Depends(get_db)):
    t = await db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    if body.status and body.status not in ("Pending", "In Progress", "Completed", "Blocked"):
        raise HTTPException(422, "Invalid status")
    try:
        await service.update_task(db, t, status=body.status, actor=body.actor, note=body.note)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return ser_task(t, await db.get(Obligation, t.obligation_id) if t.obligation_id else None)


@router.post("/tasks/{task_id}/evidence")
async def upload_evidence(task_id: uuid.UUID, file: UploadFile = File(...), note: str = Form(""),
                          actor: str = Form("Department Owner"), complete: bool = Form(False),
                          db: AsyncSession = Depends(get_db)):
    t = await db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20 MB).")
    await service.update_task(db, t, status="Completed" if complete else None, actor=actor, note=note or None,
                              file_name=file.filename, file_bytes=data)
    return ser_task(t, await db.get(Obligation, t.obligation_id) if t.obligation_id else None)


@router.get("/tasks/{task_id}/evidence/{name}")
async def get_evidence(task_id: uuid.UUID, name: str):
    path = (service.EVIDENCE_DIR / str(task_id) / name).resolve()
    if service.EVIDENCE_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(404, "Not found")
    return FileResponse(path)


# ── audit ──────────────────────────────────────────────────────────────────
@router.get("/audit")
async def list_audit(workflow_id: Optional[uuid.UUID] = None, limit: int = 300, db: AsyncSession = Depends(get_db)):
    q = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(min(limit, 1000))
    if workflow_id:
        q = q.where(AuditEvent.workflow_id == workflow_id)
    return [ser_audit(e) for e in (await db.execute(q)).scalars()]


@router.get("/audit/verify")
async def verify_audit(db: AsyncSession = Depends(get_db)):
    return await audit.verify(db)


# ── dashboard ──────────────────────────────────────────────────────────────
@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    circulars = await _doc_rows(db)
    obs = (await db.execute(select(Obligation).where(Obligation.excluded.is_(False)))).scalars().all()
    tasks = (await db.execute(select(Task))).scalars().all()
    today = date.today()
    overdue = [t for t in tasks if t.status != "Completed" and t.due_date and t.due_date < today]
    done = [t for t in tasks if t.status == "Completed"]
    pipeline = {k: 0 for k in ("RECEIVED", "ANALYSING", "AWAITING_APPROVAL", "IMPLEMENTATION", "MONITORING")}
    for c in circulars:
        pipeline[c["stage"]] += 1
    active_obs = [o for o in obs if o.status in ("active", "completed")]
    completed_obs = [o for o in active_obs if o.status == "completed"]
    # health: share of in-scope obligations completed, penalised by overdue tasks
    if active_obs:
        score = 100 * len(completed_obs) / len(active_obs)
        if tasks:
            score = 0.6 * score + 40 * (len(done) / len(tasks)) - min(30, 5 * len(overdue))
        score = max(0, min(100, round(score)))
    else:
        score = None
    recent = (await db.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(12))).scalars().all()
    risk_counts = {r: sum(1 for o in obs if (o.risk or "LOW") == r and o.status != "completed")
                   for r in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}
    return {
        "pipeline": pipeline,
        "attention": {
            "urgent_approvals": sum(c["status"] in ("pending_approval_1", "pending_approval_2") for c in circulars),
            "awaiting_review": sum(c["status"] in ("needs_ocr", "failed", "changes_requested") for c in circulars),
            "implementation_risks": len(overdue),
        },
        "health": {"score": score, "obligations_in_scope": len(active_obs), "obligations_completed": len(completed_obs),
                   "tasks_total": len(tasks), "tasks_done": len(done), "tasks_overdue": len(overdue)},
        "risk_counts": risk_counts,
        "obligations_total": len(obs),
        "circulars_total": len(circulars),
        "upcoming": [ser_task(t) for t in sorted((t for t in tasks if t.status != "Completed" and t.due_date),
                                                 key=lambda t: t.due_date)[:6]],
        "activity": [ser_audit(e) for e in recent],
        "provider": llm.provider_name(),
    }
