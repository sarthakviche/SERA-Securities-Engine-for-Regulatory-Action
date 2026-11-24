// SERA v2 API client + React Query hooks. Single source of truth for all pages.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";
const V2 = `${BASE}/api/v2`;

export type Risk = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type UiStage = "RECEIVED" | "ANALYSING" | "AWAITING_APPROVAL" | "IMPLEMENTATION" | "MONITORING";
export type WfStatus =
  | "created"
  | "in_analysis"
  | "needs_ocr"
  | "failed"
  | "changes_requested"
  | "pending_approval_1"
  | "planning"
  | "pending_approval_2"
  | "executing"
  | "compliant";

export interface CircularRow {
  id: string;
  workflow_id: string | null;
  reference: string;
  title: string;
  summary: string | null;
  source: string;
  issue_date: string | null;
  category: string | null;
  risk: Risk;
  origin: string;
  pdf_url: string | null;
  has_pdf: boolean;
  received_at: string | null;
  status: WfStatus;
  stage: UiStage;
  current_stage: string | null;
  progress: number;
  obligation_count: number;
  provider: string | null;
  error?: string | null;
  updated_at: string | null;
  analysis_meta?: Record<string, unknown> | null;
}

export interface Ambiguity {
  term: string;
  type: string;
  explanation: string;
  question: string;
}

export interface ObligationRow {
  id: string;
  workflow_id: string;
  code: string;
  title: string;
  description: string;
  category: string;
  clause_ref: string;
  source_text: string;
  page: number | null;
  deadline: string | null;
  due_date: string | null;
  frequency: string | null;
  evidence: string | null;
  risk: Risk;
  status: "pending" | "active" | "waived" | "completed";
  applicable: boolean;
  excluded: boolean;
  applicability_reason: string;
  ambiguity: Ambiguity[];
  confidence: number | null;
  department: string | null;
  owner: string | null;
  impact: ImpactMapping | null;
  circular_ref: string | null;
  circular_title?: string | null;
  workflow_status?: WfStatus;
  progress: number;
  task_count: number;
  tasks_done: number;
}

export interface EvidenceFile {
  name: string;
  size: number;
  sha256: string;
  uploaded_at: string;
  by: string;
}

export interface TaskRow {
  id: string;
  workflow_id: string;
  obligation_id: string | null;
  obligation_code: string | null;
  title: string;
  description: string | null;
  status: "Pending" | "In Progress" | "Completed" | "Overdue" | "Blocked";
  raw_status: string;
  priority: Risk | null;
  due_date: string | null;
  evidence_requirement: string | null;
  department: string | null;
  assignee: string | null;
  phase: string | null;
  evidence_note: string | null;
  evidence_files: EvidenceFile[];
  completed_at: string | null;
}

export interface ImpactMapping {
  obligation_code: string;
  obligation_title: string;
  departments: { department: string; matched: boolean; role: "primary_owner" | "contributor" | "informed" }[];
  systems: string[];
  severity: string;
  rationale: string;
}

export interface SopDraft {
  obligation_code: string;
  department: string;
  sop_title: string;
  change_type: "Add" | "Amend";
  current_text: string;
  proposed_text: string;
  citation: string;
}

export interface PlanTask {
  obligation_code: string;
  phase: string;
  title: string;
  department: string;
  due_date: string;
  priority: Risk;
  evidence_requirement: string | null;
  description: string;
}

export interface WorkflowDetail {
  circular: CircularRow;
  status: WfStatus;
  stage: UiStage;
  current_stage: string;
  progress: number;
  analysis: {
    summary: string;
    provider: string;
    obligations: number;
    applicable: number;
    ambiguities: number;
    risk: Risk;
    paragraphs: { ref: string; page: number; text: string }[];
    circular_number: string | null;
    circular_date: string | null;
    addressees: string[];
  } | null;
  impact: { mappings: ImpactMapping[]; needs_review: { obligation: string; reason: string }[] } | null;
  sops: SopDraft[] | null;
  plan: { start_date: string; phases: { name: string; description: string }[]; tasks: PlanTask[]; feedback_applied?: string } | null;
  approvals: Record<string, { decision: string; comment: string | null; by: string; at: string }>;
  history: { at: string; status: string; stage: string }[];
  plan_revision: number;
  obligations: ObligationRow[];
  tasks: TaskRow[];
}

export interface AuditRow {
  id: number;
  workflow_id: string | null;
  kind: "SYSTEM" | "AGENT" | "APPROVAL" | "EVIDENCE" | "REQUEST";
  title: string;
  detail: string | null;
  actor: string;
  payload: Record<string, unknown> | null;
  hash: string;
  prev_hash: string;
  at: string;
}

export interface Dashboard {
  pipeline: Record<UiStage, number>;
  attention: { urgent_approvals: number; awaiting_review: number; implementation_risks: number };
  health: {
    score: number | null;
    obligations_in_scope: number;
    obligations_completed: number;
    tasks_total: number;
    tasks_done: number;
    tasks_overdue: number;
  };
  risk_counts: Record<Risk, number>;
  obligations_total: number;
  circulars_total: number;
  upcoming: TaskRow[];
  activity: AuditRow[];
  provider: string;
}

export interface OrgProfile {
  name: string;
  entity_types: string[];
  departments: string[];
  systems: string[];
  officer_name: string | null;
  onboarded: boolean;
}

export interface Meta {
  provider: string;
  entity_types: { key: string; label: string }[];
  default_departments: string[];
  default_systems: string[];
  org: OrgProfile;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let r: Response;
  try {
    r = await fetch(`${V2}${path}`, init);
  } catch {
    throw new Error("Cannot reach the SERA backend. Is it running on port 8000?");
  }
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

const json = (body: unknown, method = "POST"): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const sera = {
  meta: () => req<Meta>("/meta"),
  updateOrg: (org: Omit<OrgProfile, "onboarded">) => req<OrgProfile>("/org", json(org, "PUT")),
  circulars: () => req<CircularRow[]>("/circulars"),
  upload: (file: File, source = "SEBI") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source", source);
    return req<{ document_id: string; workflow_id: string; created: boolean }>("/circulars/upload", {
      method: "POST",
      body: fd,
    });
  },
  sync: () => req<{ new: number; registered: number; seeded: number; errors: string[] }>("/circulars/sync", { method: "POST" }),
  analyze: (docId: string) => req<{ workflow_id: string; started: boolean }>(`/circulars/${docId}/analyze`, { method: "POST" }),
  pdfUrl: (docId: string) => `${V2}/circulars/${docId}/pdf`,
  workflow: (id: string) => req<WorkflowDetail>(`/workflows/${id}`),
  gate: (id: string, gate: "gate_1" | "gate_2", decision: "approved" | "rejected", comment?: string, excluded_codes?: string[]) =>
    req<{ status: WfStatus }>(`/workflows/${id}/gate/${gate}`, json({ decision, comment, excluded_codes, actor: currentActor() })),
  obligations: (includeExcluded = false) => req<ObligationRow[]>(`/obligations${includeExcluded ? "?include_excluded=true" : ""}`),
  patchObligation: (id: string, body: { excluded?: boolean; department?: string }) => req<ObligationRow>(`/obligations/${id}`, json(body, "PATCH")),
  tasks: () => req<TaskRow[]>("/tasks"),
  patchTask: (id: string, body: { status?: string; note?: string }) => req<TaskRow>(`/tasks/${id}`, json({ ...body, actor: currentActor() }, "PATCH")),
  evidence: (id: string, file: File, note: string, complete: boolean) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("note", note);
    fd.append("complete", String(complete));
    fd.append("actor", currentActor());
    return req<TaskRow>(`/tasks/${id}/evidence`, { method: "POST", body: fd });
  },
  evidenceUrl: (taskId: string, name: string) => `${V2}/tasks/${taskId}/evidence/${encodeURIComponent(name)}`,
  audit: (workflowId?: string) => req<AuditRow[]>(`/audit${workflowId ? `?workflow_id=${workflowId}` : ""}`),
  verifyAudit: () => req<{ valid: boolean; checked: number; head?: string; broken_at?: number }>("/audit/verify"),
  dashboard: () => req<Dashboard>("/dashboard"),
};

export function currentActor() {
  if (typeof window === "undefined") return "Compliance Officer";
  return localStorage.getItem("sera-actor") || "Compliance Officer";
}

// ── hooks ───────────────────────────────────────────────────────────────────
const ACTIVE = new Set<WfStatus>(["created", "in_analysis", "planning"]);

export const useMeta = () => useQuery({ queryKey: ["meta"], queryFn: sera.meta, staleTime: 60_000 });
export const useDashboard = () => useQuery({ queryKey: ["dashboard"], queryFn: sera.dashboard, refetchInterval: 8000 });
export const useCirculars = () =>
  useQuery({
    queryKey: ["circulars"],
    queryFn: sera.circulars,
    refetchInterval: (q) => (q.state.data?.some((c) => ACTIVE.has(c.status)) ? 1500 : 10000),
  });
export const useWorkflow = (id: string | null | undefined) =>
  useQuery({
    queryKey: ["workflow", id],
    queryFn: () => sera.workflow(id!),
    enabled: !!id,
    refetchInterval: (q) => (q.state.data && ACTIVE.has(q.state.data.status) ? 1200 : 8000),
  });
export const useObligations = (includeExcluded = false) =>
  useQuery({ queryKey: ["obligations", includeExcluded], queryFn: () => sera.obligations(includeExcluded) });
export const useTasks = () => useQuery({ queryKey: ["tasks"], queryFn: sera.tasks, refetchInterval: 10000 });
export const useAudit = (workflowId?: string) =>
  useQuery({ queryKey: ["audit", workflowId ?? "all"], queryFn: () => sera.audit(workflowId), refetchInterval: 10000 });

export function useInvalidateAll() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries();
}

export function useSeraMutation<TArgs, TRes>(fn: (a: TArgs) => Promise<TRes>) {
  const inv = useInvalidateAll();
  return useMutation({ mutationFn: fn, onSettled: () => inv() });
}

// ── active workflow selection (shared across pages) ───────────────────────────
const KEY = "sera-active-workflow";
const listeners = new Set<(id: string | null) => void>();

export function setActiveWorkflow(id: string | null) {
  if (typeof window !== "undefined") {
    if (id) localStorage.setItem(KEY, id);
    else localStorage.removeItem(KEY);
  }
  listeners.forEach((l) => l(id));
}

/** Selected circular workflow; falls back to the one most in need of attention. */
export function useActiveWorkflow(): [string | null, (id: string | null) => void, CircularRow[] | undefined] {
  const { data: circulars } = useCirculars();
  const [id, setId] = useState<string | null>(null);
  useEffect(() => {
    setId(localStorage.getItem(KEY));
    const l = (v: string | null) => setId(v);
    listeners.add(l);
    return () => {
      listeners.delete(l);
    };
  }, []);
  const valid = circulars?.some((c) => c.workflow_id === id) ? id : null;
  const priority: WfStatus[] = ["pending_approval_1", "pending_approval_2", "executing", "in_analysis", "compliant"];
  const fallback =
    circulars &&
    (priority.map((s) => circulars.find((c) => c.status === s)).find(Boolean)?.workflow_id ?? circulars[0]?.workflow_id ?? null);
  return [valid ?? fallback ?? null, setActiveWorkflow, circulars];
}

// ── display helpers ─────────────────────────────────────────────────────────
export const STATUS_LABEL: Record<WfStatus, string> = {
  created: "Received",
  in_analysis: "Analysing",
  needs_ocr: "Needs OCR",
  failed: "Failed",
  changes_requested: "Changes requested",
  pending_approval_1: "Gate 1 · Interpretation review",
  planning: "Planning",
  pending_approval_2: "Gate 2 · Plan review",
  executing: "Implementing",
  compliant: "Compliant",
};

export function statusTone(s: WfStatus): "success" | "warning" | "danger" | "info" | "neutral" | "brand" {
  if (s === "compliant") return "success";
  if (s === "pending_approval_1" || s === "pending_approval_2") return "warning";
  if (s === "failed" || s === "needs_ocr" || s === "changes_requested") return "danger";
  if (s === "executing") return "brand";
  if (s === "in_analysis" || s === "planning") return "info";
  return "neutral";
}

export function fmtDate(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function daysUntil(iso?: string | null) {
  if (!iso) return null;
  const d = new Date(iso + "T00:00:00").getTime();
  const t = new Date(new Date().toDateString()).getTime();
  return Math.round((d - t) / 86400000);
}

export function providerLabel(p?: string | null) {
  if (!p || p === "offline") return "Offline engine";
  if (p.startsWith("anthropic")) return `Claude (${p.split(":")[1]}) + verifier`;
  if (p.startsWith("groq")) return `Groq (${p.split(":")[1]}) + verifier`;
  return p;
}
