import type {
  ActivityItem,
  AuditEvent,
  Circular,
  ImplementationTask,
  Obligation,
} from "./types";

export const pipelineCounts = {
  RECEIVED: 14,
  ANALYSING: 8,
  AWAITING_APPROVAL: 3,
  IMPLEMENTATION: 21,
  MONITORING: 45,
};

export const attentionCounts = {
  urgentApprovals: 4,
  awaitingReview: 12,
  implementationRisks: 7,
};

export const implementationHealth = {
  score: 94.2,
  delta: 1.4,
  criticalExceptions: 2,
};

export const circulars: Circular[] = [
  {
    id: "c1",
    reference: "SEBI/HO/IMD/24/01",
    title: "Cybersecurity and Cyber Resilience Framework for Intermediaries",
    summary: "Revised cyber audit cadence and reporting timelines for MIIs.",
    source: "SEBI",
    receivedAt: "2026-07-10T09:42:00Z",
    stage: "ANALYSING",
    processingStatus: "Analyzing",
    risk: "HIGH",
    owner: "S. Miller",
  },
  {
    id: "c2",
    reference: "SEBI/HO/MIRSD/24/05",
    title: "Guidelines for Business Continuity and Disaster Recovery",
    summary: "New BCP-DR drill frequency and evidence retention requirements.",
    source: "SEBI",
    receivedAt: "2026-07-09T14:15:00Z",
    stage: "AWAITING_APPROVAL",
    processingStatus: "Flagged",
    risk: "MEDIUM",
    owner: "R. Mehta",
  },
  {
    id: "c3",
    reference: "SEBI/CIR/CFD/2024/11",
    title: "Master Circular on Corporate Governance for Listed Entities",
    summary: "Consolidation of governance obligations, quarterly filings.",
    source: "SEBI",
    receivedAt: "2026-07-08T11:05:00Z",
    stage: "IMPLEMENTATION",
    processingStatus: "Completed",
    risk: "LOW",
    owner: "A. Kapoor",
  },
  {
    id: "c4",
    reference: "RBI/2026-27/17",
    title: "Digital Lending Guidelines Update",
    summary: "New thresholds for default loss guarantee (DLG) arrangements.",
    source: "RBI",
    receivedAt: "2026-07-07T08:30:00Z",
    stage: "MONITORING",
    processingStatus: "Completed",
    risk: "LOW",
    owner: "V. Rao",
  },
  {
    id: "c5",
    reference: "SEBI/HO/MRD/2026/104",
    title: "Cybersecurity Framework for Market Infrastructure Institutions",
    summary: "Mandatory reporting timelines for data breaches reduced.",
    source: "SEBI",
    receivedAt: "2026-07-06T16:50:00Z",
    stage: "ANALYSING",
    processingStatus: "Analyzing",
    risk: "HIGH",
    owner: "S. Miller",
  },
  {
    id: "c6",
    reference: "SEBI/HO/CFD/2026/22",
    title: "Quarterly Compliance Filing Extensions",
    summary: "Submission deadline for Form A-12 moved to Nov 15th.",
    source: "SEBI",
    receivedAt: "2026-07-05T08:30:00Z",
    stage: "MONITORING",
    processingStatus: "Completed",
    risk: "LOW",
  },
];

export const obligations: Obligation[] = [
  {
    id: "o1",
    code: "OB-001",
    title: "Cyber Security Committee Formation",
    description:
      "Formation of a board-level committee led by a technical Non-Executive Director. Deadline: 90 days.",
    circularRef: "SEBI/HO/MRD/2026/104",
    owner: "Sarah Miller",
    department: "Compliance",
    dueDate: "2026-10-13",
    status: "In Progress",
    risk: "HIGH",
    progress: 45,
  },
  {
    id: "o2",
    code: "OB-042",
    title: "Annual Third-Party Audit",
    description: "Independent audit of ICT third-party providers with evidence pack.",
    circularRef: "DORA Art. 17",
    owner: "Mark Thorogood",
    department: "Risk",
    dueDate: "2026-09-01",
    status: "Open",
    risk: "MEDIUM",
    progress: 10,
  },
  {
    id: "o3",
    code: "OB-043",
    title: "Contractual Clause Revision — Vendor",
    description: "Update vendor MSAs with DORA-aligned exit and audit clauses.",
    circularRef: "DORA Art. 17",
    owner: "A. Kapoor",
    department: "Legal",
    dueDate: "2026-08-20",
    status: "In Progress",
    risk: "MEDIUM",
    progress: 60,
  },
  {
    id: "o4",
    code: "OB-105",
    title: "BCP-DR Drill — Q3",
    description: "Perform tabletop DR drill and archive raw output.",
    circularRef: "SEBI/HO/MIRSD/24/05",
    owner: "V. Rao",
    department: "Operations",
    dueDate: "2026-07-31",
    status: "Blocked",
    risk: "HIGH",
    progress: 20,
  },
  {
    id: "o5",
    code: "OB-118",
    title: "Basel III LCR Reporting — Q3",
    description: "Verified compliant filing for Q3 reporting cycle.",
    circularRef: "RBI/2026-27/17",
    owner: "Sarah Miller",
    department: "Treasury",
    dueDate: "2026-06-30",
    status: "Compliant",
    risk: "LOW",
    progress: 100,
  },
];

export const tasks: ImplementationTask[] = [
  { id: "t1", obligationId: "o1", title: "Draft committee charter", assignee: "S. Miller", status: "Done", dueDate: "2026-07-20", progress: 100 },
  { id: "t2", obligationId: "o1", title: "Identify board NED candidate", assignee: "A. Kapoor", status: "In Progress", dueDate: "2026-08-05", progress: 55 },
  { id: "t3", obligationId: "o1", title: "Board resolution & filing", assignee: "R. Mehta", status: "Todo", dueDate: "2026-09-10", progress: 0 },
  { id: "t4", obligationId: "o2", title: "Scope vendor list", assignee: "M. Thorogood", status: "In Progress", dueDate: "2026-07-30", progress: 40 },
  { id: "t5", obligationId: "o3", title: "Redline MSA template", assignee: "Legal Ops", status: "Review", dueDate: "2026-07-25", progress: 80 },
  { id: "t6", obligationId: "o4", title: "Resolve infra dependency", assignee: "V. Rao", status: "Todo", dueDate: "2026-07-28", progress: 10 },
];

export const auditEvents: AuditEvent[] = [
  {
    id: "a1",
    kind: "APPROVAL",
    title: "Compliance Register Updated",
    detail:
      "The obligation for Basel III: Liquidity Coverage Ratio Reporting has been officially verified as COMPLIANT for the Q3 reporting cycle.",
    actor: "Sarah J. Miller (Senior Compliance Officer)",
    at: "2026-07-12T09:42:00Z",
    hash: "8f2a…9c11",
  },
  {
    id: "a2",
    kind: "EVIDENCE",
    title: "Document Verification: Tier 1 Capital Evidence",
    detail:
      "Automated consistency check passed. Human reviewer confirmed matching attributes between ledger records and submitted PDF artifacts.",
    actor: "R. Mehta",
    at: "2026-07-10T14:15:00Z",
    attachments: [
      { name: "Q3_Tier1_Report_Final.pdf", size: "4.2 MB", verified: true },
      { name: "Ledger_Extract_0923.csv", size: "12.8 MB", verified: true },
    ],
  },
  {
    id: "a3",
    kind: "REQUEST",
    title: "Additional Evidence Requested",
    detail:
      "The submitted narrative does not explicitly cover the intra-day liquidity stress testing scenarios defined in Annex IV. Please provide the raw output of the stress test runner.",
    actor: "Treasury Operations",
    at: "2026-07-08T11:04:00Z",
  },
];

export const activity: ActivityItem[] = [
  {
    id: "act1",
    kind: "APPROVED",
    title: "Obligation Approved",
    detail: "Devansh approved SEBI/24 Master Circular implementation plan.",
    at: "2026-07-12T14:20:00Z",
  },
  {
    id: "act2",
    kind: "ANALYZED",
    title: "Circular Analyzed",
    detail: "AI Agent parsed cybersecurity framework for Brokerage Division.",
    at: "2026-07-12T11:05:00Z",
  },
  {
    id: "act3",
    kind: "ASSIGNED",
    title: "Assigned Task",
    detail: "Rohan Mehta assigned to Compliance Audit – Q3.",
    at: "2026-07-12T09:45:00Z",
  },
];

export const nav = [
  { to: "/", label: "Dashboard", icon: "LayoutDashboard" },
  { to: "/inbox", label: "Regulatory Inbox", icon: "Inbox" },
  { to: "/workspace", label: "Regulatory Workspace", icon: "Layers" },
  { to: "/obligations", label: "Obligations", icon: "ClipboardCheck" },
  { to: "/impact-map", label: "Impact Map", icon: "Network" },
  { to: "/implementation-plan", label: "Implementation Plan", icon: "Workflow" },
  { to: "/implementation-tracker", label: "Implementation Tracker", icon: "LineChart" },
  { to: "/compliance-register", label: "Compliance Register", icon: "ShieldCheck" },
  { to: "/audit-trail", label: "Audit Trail", icon: "History" },
] as const;
