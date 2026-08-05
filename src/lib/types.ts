// Domain models for SERA. Kept UI-agnostic so a real API can slot in later.

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type PipelineStage =
  | "RECEIVED"
  | "ANALYSING"
  | "AWAITING_APPROVAL"
  | "IMPLEMENTATION"
  | "MONITORING";
export type ProcessingStatus = "Analyzing" | "Flagged" | "Completed" | "Pending";
export type ObligationStatus = "Open" | "In Progress" | "Blocked" | "Compliant" | "Overdue";
export type TaskStatus = "Todo" | "In Progress" | "Review" | "Done";
export type RegSource = "SEBI" | "RBI" | "IRDAI" | "MCA" | "FIU";

export interface Circular {
  id: string;
  reference: string;
  title: string;
  summary: string;
  source: RegSource;
  receivedAt: string;
  stage: PipelineStage;
  processingStatus: ProcessingStatus;
  risk: RiskLevel;
  owner?: string;
}

export interface Obligation {
  id: string;
  code: string;
  title: string;
  description: string;
  circularRef: string;
  owner: string;
  department: string;
  dueDate: string;
  status: ObligationStatus;
  risk: RiskLevel;
  progress: number; // 0-100
}

export interface ImplementationTask {
  id: string;
  obligationId: string;
  title: string;
  assignee: string;
  status: TaskStatus;
  dueDate: string;
  progress: number;
}

export interface AuditEvent {
  id: string;
  kind: "APPROVAL" | "EVIDENCE" | "REQUEST" | "SYSTEM";
  title: string;
  detail: string;
  actor: string;
  at: string;
  hash?: string;
  attachments?: { name: string; size: string; verified: boolean }[];
}

export interface ActivityItem {
  id: string;
  kind: "APPROVED" | "ANALYZED" | "ASSIGNED" | "FLAGGED";
  title: string;
  detail: string;
  at: string;
}
