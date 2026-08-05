import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Circular, Obligation, ImplementationTask, AuditEvent, ActivityItem } from "./types";

export type DemoStage =
  | "OFF"
  | "DETECTED"
  | "ANALYZED"
  | "INTERPRETATION_APPROVED"
  | "IMPACT_MAPPED"
  | "PLAN_APPROVED"
  | "IMPLEMENTING"
  | "EVIDENCE_REVIEW"
  | "COMPLIANT";

export interface DemoContextType {
  demoStage: DemoStage;
  setDemoStage: (stage: DemoStage) => void;
  resetDemo: () => void;
  advanceDemo: () => void;
  isDemoActive: boolean;
  circulars: Circular[];
  obligations: Obligation[];
  tasks: ImplementationTask[];
  auditEvents: AuditEvent[];
  activity: ActivityItem[];
  pipelineCounts: {
    RECEIVED: number;
    ANALYSING: number;
    AWAITING_APPROVAL: number;
    IMPLEMENTATION: number;
    MONITORING: number;
  };
  attentionCounts: {
    urgentApprovals: number;
    awaitingReview: number;
    implementationRisks: number;
  };
  implementationHealth: {
    score: number;
    delta: number;
    criticalExceptions: number;
  };
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

// Fictional SEBI circular
export const demoCircular: Circular = {
  id: "c-demo",
  reference: "SEBI/HO/MIRSD/2026/104",
  title: "Periodic Re-verification of Registered Client Mobile Numbers",
  summary: "Mandatory periodic re-verification of registered client mobile numbers every 12 months (previously 24 months) and retention of verification records.",
  source: "SEBI",
  receivedAt: "2026-07-14T09:00:00Z",
  stage: "RECEIVED",
  processingStatus: "Analyzing",
  risk: "HIGH",
  owner: "Sarah Miller",
};

// Obligation derived from circular
export const demoObligation: Obligation = {
  id: "o-demo",
  code: "OB-MIRSD-104",
  title: "Periodic Client Mobile Re-verification",
  description: "Verify registered client mobile numbers every 12 months using an authenticated mechanism and retain logs.",
  circularRef: "SEBI/HO/MIRSD/2026/104",
  owner: "Sarah Miller",
  department: "Compliance",
  dueDate: "2026-10-01",
  status: "Open",
  risk: "HIGH",
  progress: 0,
};

// Seed baseline lists from original mock data
import {
  circulars as defaultCirculars,
  obligations as defaultObligations,
  tasks as defaultTasks,
  auditEvents as defaultAuditEvents,
  activity as defaultActivity,
  pipelineCounts as defaultPipelineCounts,
  attentionCounts as defaultAttentionCounts,
  implementationHealth as defaultImplementationHealth,
} from "./mock-data";

export function DemoProvider({ children }: { children: ReactNode }) {
  const [demoStage, setDemoStageState] = useState<DemoStage>("OFF");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("sera-demo-stage") as DemoStage | null;
      if (stored) {
        setDemoStageState(stored);
      }
    }
  }, []);

  const setDemoStage = (stage: DemoStage) => {
    setDemoStageState(stage);
    localStorage.setItem("sera-demo-stage", stage);
  };

  const resetDemo = () => {
    setDemoStage("OFF");
  };

  const advanceDemo = () => {
    if (demoStage === "PLAN_APPROVED") {
      setDemoStage("IMPLEMENTING");
    } else if (demoStage === "IMPLEMENTING") {
      setDemoStage("EVIDENCE_REVIEW");
    } else if (demoStage === "EVIDENCE_REVIEW") {
      setDemoStage("COMPLIANT");
    }
  };

  const isDemoActive = demoStage !== "OFF";

  // Derive circulars based on stage
  let activeCirculars = [...defaultCirculars];
  if (isDemoActive) {
    const stageCircular = { ...demoCircular };
    if (demoStage === "DETECTED") {
      stageCircular.stage = "RECEIVED";
      stageCircular.processingStatus = "Analyzing";
    } else if (demoStage === "ANALYZED") {
      stageCircular.stage = "ANALYSING";
      stageCircular.processingStatus = "Flagged";
    } else if (demoStage === "INTERPRETATION_APPROVED" || demoStage === "IMPACT_MAPPED") {
      stageCircular.stage = "AWAITING_APPROVAL";
      stageCircular.processingStatus = "Completed";
    } else if (
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW"
    ) {
      stageCircular.stage = "IMPLEMENTATION";
      stageCircular.processingStatus = "Completed";
    } else {
      stageCircular.stage = "MONITORING";
      stageCircular.processingStatus = "Completed";
    }
    activeCirculars = [stageCircular, ...defaultCirculars];
  }

  // Derive obligations based on stage
  let activeObligations = [...defaultObligations];
  if (isDemoActive && demoStage !== "DETECTED" && demoStage !== "ANALYZED") {
    const stageObligation = { ...demoObligation };
    if (demoStage === "INTERPRETATION_APPROVED") {
      stageObligation.status = "Open";
      stageObligation.progress = 0;
    } else if (demoStage === "IMPACT_MAPPED") {
      stageObligation.status = "In Progress";
      stageObligation.progress = 15;
    } else if (demoStage === "PLAN_APPROVED") {
      stageObligation.status = "In Progress";
      stageObligation.progress = 30;
    } else if (demoStage === "IMPLEMENTING") {
      stageObligation.status = "In Progress";
      stageObligation.progress = 65;
    } else if (demoStage === "EVIDENCE_REVIEW") {
      stageObligation.status = "Blocked"; // Mocking waiting for evidence verification
      stageObligation.progress = 90;
    } else if (demoStage === "COMPLIANT") {
      stageObligation.status = "Compliant";
      stageObligation.progress = 100;
    }
    activeObligations = [stageObligation, ...defaultObligations];
  }

  // Derive tasks
  let activeTasks = [...defaultTasks];
  if (
    isDemoActive &&
    demoStage !== "DETECTED" &&
    demoStage !== "ANALYZED" &&
    demoStage !== "INTERPRETATION_APPROVED" &&
    demoStage !== "IMPACT_MAPPED"
  ) {
    const demoTasks: ImplementationTask[] = [
      {
        id: "t-demo-it1",
        obligationId: "o-demo",
        title: "Change re-verification scheduler from 24 months to 12 months",
        assignee: "IT Dept",
        status:
          demoStage === "PLAN_APPROVED"
            ? "In Progress"
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? "Done"
              : "Todo",
        dueDate: "2026-09-15",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 30
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? 100
              : 0,
      },
      {
        id: "t-demo-it2",
        obligationId: "o-demo",
        title: "Configure authenticated OTP verification workflow in Mobile App/CRM",
        assignee: "IT Dept",
        status:
          demoStage === "PLAN_APPROVED"
            ? "Todo"
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? "Done"
              : "Todo",
        dueDate: "2026-09-20",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 0
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? 100
              : 0,
      },
      {
        id: "t-demo-it3",
        obligationId: "o-demo",
        title: "Store verification timestamps and outcomes in database logs",
        assignee: "Database Admin",
        status:
          demoStage === "PLAN_APPROVED"
            ? "Todo"
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? "Done"
              : "Todo",
        dueDate: "2026-09-22",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 0
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? 100
              : 0,
      },
      {
        id: "t-demo-ops1",
        obligationId: "o-demo",
        title: "Update the Client Mobile Verification SOP to 12 months",
        assignee: "Operations Team",
        status:
          demoStage === "PLAN_APPROVED"
            ? "In Progress"
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? "Done"
              : "Todo",
        dueDate: "2026-09-01",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 50
            : demoStage === "IMPLEMENTING" || demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
              ? 100
              : 0,
      },
      {
        id: "t-demo-cust1",
        obligationId: "o-demo",
        title: "Prepare customer reminder communications and escalation templates",
        assignee: "Customer Ops",
        status:
          demoStage === "PLAN_APPROVED"
            ? "Todo"
            : demoStage === "IMPLEMENTING"
              ? "In Progress"
              : demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
                ? "Done"
                : "Todo",
        dueDate: "2026-09-25",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 0
            : demoStage === "IMPLEMENTING"
              ? 60
              : demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
                ? 100
                : 0,
      },
      {
        id: "t-demo-qa1",
        obligationId: "o-demo",
        title: "Perform end-to-end testing of OTP verification workflows",
        assignee: "QA Team",
        status:
          demoStage === "PLAN_APPROVED"
            ? "Todo"
            : demoStage === "IMPLEMENTING"
              ? "In Progress"
              : demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
                ? "Done"
                : "Todo",
        dueDate: "2026-09-28",
        progress:
          demoStage === "PLAN_APPROVED"
            ? 0
            : demoStage === "IMPLEMENTING"
              ? 40
              : demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT"
                ? 100
                : 0,
      },
      {
        id: "t-demo-comp1",
        obligationId: "o-demo",
        title: "Validate and audit compliance evidence against circular requirements",
        assignee: "Sarah Miller",
        status:
          demoStage === "PLAN_APPROVED" || demoStage === "IMPLEMENTING"
            ? "Todo"
            : demoStage === "EVIDENCE_REVIEW"
              ? "Review"
              : demoStage === "COMPLIANT"
                ? "Done"
                : "Todo",
        dueDate: "2026-09-30",
        progress:
          demoStage === "PLAN_APPROVED" || demoStage === "IMPLEMENTING"
            ? 0
            : demoStage === "EVIDENCE_REVIEW"
              ? 80
              : demoStage === "COMPLIANT"
                ? 100
                : 0,
      },
    ];
    activeTasks = [...demoTasks, ...defaultTasks];
  }

  // Derive audit events
  let activeAuditEvents = [...defaultAuditEvents];
  if (isDemoActive) {
    const demoEvents: AuditEvent[] = [];

    if (
      demoStage === "DETECTED" ||
      demoStage === "ANALYZED" ||
      demoStage === "INTERPRETATION_APPROVED" ||
      demoStage === "IMPACT_MAPPED" ||
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoEvents.push({
        id: "audit-demo1",
        kind: "SYSTEM",
        title: "Circular Detected: SEBI/HO/MIRSD/2026/104",
        detail: "Automated crawler identified a new circular from SEBI. Ingestion pipeline initiated.",
        actor: "SERA Crawler Service",
        at: "2026-07-14T09:00:00Z",
      });
    }

    if (
      demoStage === "ANALYZED" ||
      demoStage === "INTERPRETATION_APPROVED" ||
      demoStage === "IMPACT_MAPPED" ||
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoEvents.push({
        id: "audit-demo2",
        kind: "SYSTEM",
        title: "Ingestion & Analysis Completed",
        detail: "AI extraction engine successfully parsed text, identified Stockbroker applicability, and highlighted key delta changes.",
        actor: "SERA AI Parser",
        at: "2026-07-14T09:02:00Z",
      });
    }

    if (
      demoStage === "INTERPRETATION_APPROVED" ||
      demoStage === "IMPACT_MAPPED" ||
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoEvents.push(
        {
          id: "audit-demo3",
          kind: "APPROVAL",
          title: "AI Analysis Approved & Committed",
          detail: "Compliance Officer Devansh Narlawar approved the AI regulatory interpretation.",
          actor: "Devansh Narlawar (Compliance Officer)",
          at: "2026-07-14T10:15:00Z",
        },
        {
          id: "audit-demo4",
          kind: "SYSTEM",
          title: "Obligation Registered: OB-MIRSD-104",
          detail: "Mandate formally committed to active obligations register with 'High' risk level and 12-month re-verification constraint.",
          actor: "SERA Compliance Core",
          at: "2026-07-14T10:16:00Z",
        }
      );
    }

    if (
      demoStage === "IMPACT_MAPPED" ||
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoEvents.push({
        id: "audit-demo5",
        kind: "SYSTEM",
        title: "Impact Mappings Confirmed",
        detail: "System relationships confirmed for Periodic KYC process, client profiles, CRM, and Mobile OTP delivery flows.",
        actor: "Devansh Narlawar (Compliance Officer)",
        at: "2026-07-14T10:30:00Z",
      });
    }

    if (
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoEvents.push({
        id: "audit-demo6",
        kind: "APPROVAL",
        title: "Implementation Plan Approved",
        detail: "Action tasks assigned to IT, Operations, Customer Operations, and QA. Before/after SOP amendment diff locked.",
        actor: "Devansh Narlawar (Compliance Officer)",
        at: "2026-07-14T11:00:00Z",
      });
    }

    if (demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT") {
      demoEvents.push({
        id: "audit-demo7",
        kind: "EVIDENCE",
        title: "Evidence Uploaded & Checked",
        detail: "Validation artifacts and configuration proofs submitted for compliance assessment.",
        actor: "IT & Operations Teams",
        at: "2026-07-15T15:30:00Z",
        attachments: [
          { name: "SOP_Client_Mobile_v2.pdf", size: "1.4 MB", verified: true },
          { name: "Config_Change_Scheduler.log", size: "256 KB", verified: true },
          { name: "QA_Test_Report_OTP.pdf", size: "2.1 MB", verified: true },
        ],
      });
    }

    if (demoStage === "COMPLIANT") {
      demoEvents.push({
        id: "audit-demo8",
        kind: "APPROVAL",
        title: "Obligation Verified Compliant",
        detail: "Devansh Narlawar verified all proof records. Obligation has been promoted to continuous compliance monitoring status.",
        actor: "Devansh Narlawar (Compliance Officer)",
        at: "2026-07-16T10:00:00Z",
        hash: "7b4f…c889",
      });
    }

    activeAuditEvents = [...demoEvents, ...defaultAuditEvents];
  }

  // Derive activity
  let activeActivity = [...defaultActivity];
  if (isDemoActive) {
    const demoActivity: ActivityItem[] = [];

    if (demoStage === "DETECTED" || demoStage === "ANALYZED") {
      demoActivity.push({
        id: "act-demo-1",
        kind: "ANALYZED",
        title: "Analyzing Circular",
        detail: "AI Engine analyzing client re-verification changes for Brokerage division.",
        at: "2026-07-14T09:02:00Z",
      });
    }

    if (
      demoStage === "INTERPRETATION_APPROVED" ||
      demoStage === "IMPACT_MAPPED" ||
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoActivity.push({
        id: "act-demo-2",
        kind: "APPROVED",
        title: "Obligation Registered",
        detail: "Client Mobile Re-verification obligation OB-MIRSD-104 created and approved.",
        at: "2026-07-14T10:15:00Z",
      });
    }

    if (
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW" ||
      demoStage === "COMPLIANT"
    ) {
      demoActivity.push({
        id: "act-demo-3",
        kind: "ASSIGNED",
        title: "Implementation Tasks Assigned",
        detail: "7 tasks assigned to IT, Operations, QA, and Compliance.",
        at: "2026-07-14T11:00:00Z",
      });
    }

    if (demoStage === "COMPLIANT") {
      demoActivity.push({
        id: "act-demo-4",
        kind: "APPROVED",
        title: "Obligation Compliant",
        detail: "OB-MIRSD-104 verified compliant and active under continuous monitoring.",
        at: "2026-07-16T10:00:00Z",
      });
    }

    activeActivity = [...demoActivity, ...defaultActivity];
  }

  // Derive metrics
  const activePipelineCounts = { ...defaultPipelineCounts };
  const activeAttentionCounts = { ...defaultAttentionCounts };
  const activeImplementationHealth = { ...defaultImplementationHealth };

  if (isDemoActive) {
    if (demoStage === "DETECTED") {
      activePipelineCounts.RECEIVED += 1;
      activeAttentionCounts.awaitingReview += 1;
    } else if (demoStage === "ANALYZED") {
      activePipelineCounts.ANALYSING += 1;
      activeAttentionCounts.awaitingReview += 1;
    } else if (demoStage === "INTERPRETATION_APPROVED" || demoStage === "IMPACT_MAPPED") {
      activePipelineCounts.AWAITING_APPROVAL += 1;
      activeAttentionCounts.urgentApprovals += 1;
    } else if (
      demoStage === "PLAN_APPROVED" ||
      demoStage === "IMPLEMENTING" ||
      demoStage === "EVIDENCE_REVIEW"
    ) {
      activePipelineCounts.IMPLEMENTATION += 1;
      activeAttentionCounts.implementationRisks += 1;
      if (demoStage === "EVIDENCE_REVIEW") {
        // High risk waiting for compliance verification
        activeAttentionCounts.urgentApprovals += 1;
      }
    } else if (demoStage === "COMPLIANT") {
      activePipelineCounts.MONITORING += 1;
      activeImplementationHealth.score = 95.8;
      activeImplementationHealth.delta = 1.6;
      activeImplementationHealth.criticalExceptions = 1; // Mapped exception resolved
    }
  }

  return (
    <DemoContext.Provider
      value={{
        demoStage,
        setDemoStage,
        resetDemo,
        advanceDemo,
        isDemoActive,
        circulars: activeCirculars,
        obligations: activeObligations,
        tasks: activeTasks,
        auditEvents: activeAuditEvents,
        activity: activeActivity,
        pipelineCounts: activePipelineCounts,
        attentionCounts: activeAttentionCounts,
        implementationHealth: activeImplementationHealth,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  const context = useContext(DemoContext);
  if (context === undefined) {
    throw new Error("useDemo must be used within a DemoProvider");
  }
  return context;
}
