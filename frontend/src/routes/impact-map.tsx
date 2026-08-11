import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Lock, Loader2, Plus, Download, ArrowRight } from "lucide-react";
import { useDemo } from "@/lib/demo";
import { toast } from "sonner";
import { useWorkflow } from "@/hooks/useWorkflow";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";
import { AgentStatusBanner } from "@/components/sera/agent-status-banner";
import { ImpactGraph, ImpactNode } from "@/components/sera/impact-graph";

export const Route = createFileRoute("/impact-map")({
  head: () => ({ meta: [{ title: "Impact Map · SERA" }] }),
  component: ImpactMap,
});

// Fictional SEBI scenario nodes
const demoNodes = [
  { col: "clause", code: "CLAUSE 2", title: "12M Re-verification Mandate", highlight: true },
  { col: "obligation", code: "OB-MIRSD-104", title: "Periodic Mobile Re-verification" },
  { col: "process", code: "PROC-KYC-01", title: "Periodic KYC Profile Maintenance" },
  { col: "system", code: "SYS-CRM", title: "CRM Client Records" },
  { col: "system", code: "SYS-APP", title: "Mobile Client App" },
  { col: "system", code: "SYS-SMS", title: "SMS Gateway Service" },
  { col: "department", code: "", title: "IT Infrastructure" },
  { col: "department", code: "", title: "Operations Queue" },
  { col: "owner", code: "", title: "Sarah Miller (Ops)" },
  { col: "owner", code: "", title: "IT Admin Team (IT)" },
  { col: "evidence", code: "DOC-SOP-104", title: "Client Verification SOP v2.0" },
  { col: "evidence", code: "LOG-OTP", title: "SMS OTP Verification Logs" },
];

// Baseline DORA nodes
const defaultNodes = [
  { col: "clause", code: "ART 17.1", title: "Risk Assessment Strategy", highlight: true },
  { col: "obligation", code: "OB-042", title: "Annual Third-Party Audit" },
  { col: "obligation", code: "OB-043", title: "Contractual Clause Rev." },
  { col: "process", code: "PROC-VND-01", title: "Vendor Onboarding" },
  { col: "system", code: "SYS-GRC", title: "Archer GRC Platform" },
  { col: "system", code: "SYS-ERP", title: "SAP Vendor Portal" },
  { col: "department", code: "", title: "Procurement" },
  { col: "department", code: "", title: "Risk & Compliance" },
  { col: "owner", code: "", title: "Sarah Jenkins" },
  { col: "owner", code: "", title: "Mark Thorogood" },
  { col: "evidence", code: "DOC-AUDIT-23", title: "Annual Report 2023" },
];

function ImpactMap() {
  const { demoStage, setDemoStage, isDemoActive, workflowId } = useDemo();
  const navigate = useNavigate();
  const { data: workflowStatus } = useWorkflow(workflowId);
  const [realNodes, setRealNodes] = useState<ImpactNode[] | null>(null);

  useEffect(() => {
    // If agent is done mapping, fetch its output
    if (workflowId && workflowStatus && workflowStatus.current_stage !== "impact_mapping") {
      api.getAgentOutput(workflowId, "impact_mapping_agent")
        .then((output) => {
          if (output && output.mappings) {
            const nodes: ImpactNode[] = [];
            // Parse real output into nodes
            // Assume single clause for now (TODO: get from document metadata)
            nodes.push({ col: "clause", code: "CLAUSE", title: "Re-verification Mandate", highlight: true });
            
            output.mappings.forEach((m: any) => {
              nodes.push({ col: "obligation", code: m.obligation_id?.substring(0, 8), title: "Mapped Obligation" });
              m.affected_departments?.forEach((d: any) => {
                nodes.push({ col: "department", title: d.department_name_suggested });
              });
              m.affected_systems?.forEach((s: any) => {
                nodes.push({ col: "system", title: s.system_name });
              });
              if (m.evidence_required) {
                 nodes.push({ col: "evidence", title: m.evidence_required.substring(0,30) + "..." });
              }
            });
            setRealNodes(nodes);
          }
        })
        .catch(console.error);
    }
  }, [workflowId, workflowStatus]);

  const handleConfirmMapping = () => {
    setDemoStage("IMPACT_MAPPED");
    toast.success("Impact Mapping Confirmed", {
      description: "Propagation relationships mapped. Proceeding to Implementation Plan.",
    });
    navigate({ to: "/implementation-plan" });
  };

  const isMapping = workflowStatus?.current_stage === "impact_mapping";
  const currentNodes = realNodes || (isDemoActive ? demoNodes : defaultNodes);

  return (
    <AppShell>
      <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
        <span>Workspace</span>
        <span>/</span>
        <span className="text-foreground">Impact Mapping</span>
      </div>

      <PageHeader
        title="Regulatory Impact Graph"
        description={
          isDemoActive
            ? "SEBI Circular SEBI/HO/MIRSD/2026/104: Client Mobile Re-verification Scope Mapping"
            : "DORA Article 17: ICT Third-Party Risk Management Framework"
        }
        actions={
          <>
            {isDemoActive && !workflowId && (
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Scenario Map
              </span>
            )}
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" /> Export PDF
            </Button>
            <Button className="gap-2">
              <Plus className="h-4 w-4" /> New Mapping
            </Button>
          </>
        }
      />

      {isMapping && (
        <AgentStatusBanner
          icon={<Loader2 className="animate-spin" />}
          message="SERA is mapping obligations to departments and systems..."
          subtext="This usually takes under 30 seconds."
        />
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Node graph mapping visualization */}
        <div className="relative">
          <ImpactGraph nodes={currentNodes} />
          {isMapping && (
            <div className="absolute inset-0 bg-background/50 backdrop-blur-[1px] rounded-2xl flex items-center justify-center">
            </div>
          )}
        </div>

        {/* Dynamic Sidebar based on active stage */}
        <aside className="space-y-4">
          <Card className="rounded-2xl p-5 bg-card border-border">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="text-base font-semibold text-foreground">Impact Summary</div>
              <StatusPill tone="danger">HIGH IMPACT</StatusPill>
            </div>
            <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Primary Circular Affected
            </div>
            <Card className="mt-1.5 rounded-xl bg-surface-2 p-3 shadow-none border border-border">
              <div className="text-xs font-semibold text-foreground">
                {isDemoActive ? "SEBI/HO/MIRSD/2026/104" : "DORA Regulation (EU) 2022/2554"}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                {isDemoActive
                  ? "Periodic Re-verification of Registered Client Mobile Numbers"
                  : "ICT Third-Party Risk Management Framework"}
              </div>
            </Card>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <Card className="rounded-xl p-3 text-center shadow-none border border-border bg-background">
                <div className="text-[9px] uppercase tracking-wide text-muted-foreground font-semibold">
                  Affected Systems
                </div>
                <div className="mt-1 text-xl font-bold text-foreground">
                  {isDemoActive ? "03" : "02"}
                </div>
              </Card>
              <Card className="rounded-xl p-3 text-center shadow-none border border-border bg-background">
                <div className="text-[9px] uppercase tracking-wide text-muted-foreground font-semibold">
                  Impacted SOPs
                </div>
                <div className="mt-1 text-xl font-bold text-foreground">
                  {isDemoActive ? "01" : "01"}
                </div>
              </Card>
            </div>

            <div className="mt-4">
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Mapping Completeness</span>
                <span className="font-semibold text-primary">{isMapping ? "0%" : "100%"}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-primary transition-all duration-1000" style={{ width: isMapping ? "0%" : "100%" }} />
              </div>
              <div className="mt-1 text-[10px] text-muted-foreground">
                {isMapping ? "AI Agent is determining impacts..." : "All nodes mapped & verified"}
              </div>
            </div>
          </Card>

          <Card className="rounded-2xl p-5 bg-card border-border">
            <div className="text-base font-semibold text-foreground border-b border-border pb-3 mb-3">
              Propagation Rationale
            </div>
            {isDemoActive && !isMapping ? (
              <ol className="space-y-4 border-l border-border pl-5 relative text-xs leading-relaxed">
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                  tone="done"
                  title="Circular &rarr; Obligation"
                  detail="SEBI Clause 2 reduces verification interval to 12 months, creating the obligation OB-MIRSD-104."
                />
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                  tone="done"
                  title="Obligation &rarr; Process"
                  detail="Re-verification directly impacts the Client Profile Maintenance & KYC Operational Process."
                />
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
                  tone="done"
                  title="Process &rarr; Systems"
                  detail="SMS Gateway sends OTPs, Mobile App takes client inputs, and CRM DB stores timestamps."
                />
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                  tone="done"
                  title="Process &rarr; SOP & Evidence"
                  detail="Requires amending client KYC SOP and storing verification logs as compliance proof."
                />
              </ol>
            ) : isMapping ? (
              <ol className="space-y-4 border-l border-border pl-5 relative text-xs leading-relaxed opacity-50">
                <PathStep
                  icon={<Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  tone="active"
                  title="Analyzing Propagation..."
                  detail="Agent is tracing obligation impacts."
                />
              </ol>
            ) : (
              <ol className="space-y-4 border-l border-border pl-5 relative text-xs leading-relaxed">
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                  tone="done"
                  title="Requirement Identified"
                  detail="Clause ART 17.1 requires mandatory risk scoping for all cloud providers."
                />
                <PathStep
                  icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                  tone="done"
                  title="Process Impacted"
                  detail="Procurement Onboarding updated with DORA-specific checklists."
                />
                <PathStep
                  icon={<Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  tone="active"
                  title="System Integration Pending"
                  detail="Archer GRC module integration with SAP Vendor Portal in progress."
                />
                <PathStep
                  icon={<Lock className="h-3.5 w-3.5" />}
                  tone="idle"
                  title="Owner Approval Required"
                  detail="Waiting for sign-off from Head of Risk (Sarah J.)."
                />
              </ol>
            )}

            {isDemoActive && (
              <div className="mt-5 border-t border-border pt-4">
                {demoStage === "INTERPRETATION_APPROVED" || isMapping ? (
                  <Button
                    disabled={isMapping}
                    onClick={handleConfirmMapping}
                    className="w-full gap-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-none cursor-pointer text-xs"
                  >
                    {isMapping ? "AI is Mapping..." : "Confirm Impact Mapping"} <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                ) : (
                  <Link
                    to="/implementation-plan"
                    className="w-full inline-flex h-9 items-center justify-center rounded-md bg-secondary text-xs font-semibold text-secondary-foreground hover:bg-secondary/80"
                  >
                    Go to Implementation Plan <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                  </Link>
                )}
              </div>
            )}
          </Card>
        </aside>
      </div>
    </AppShell>
  );
}

function PathStep({
  icon,
  tone,
  title,
  detail,
}: {
  icon: React.ReactNode;
  tone: "done" | "active" | "idle";
  title: string;
  detail: string;
}) {
  const cls =
    tone === "done"
      ? "bg-primary text-primary-foreground"
      : tone === "active"
        ? "bg-info text-info-foreground"
        : "bg-muted text-muted-foreground";
  return (
    <li className="relative">
      <span className={`absolute -left-[26px] top-0.5 flex h-5 w-5 items-center justify-center rounded-full ${cls}`}>
        {icon}
      </span>
      <div className="text-sm font-semibold text-foreground">{title}</div>
      <p className="mt-0.5 text-[11px] text-muted-foreground leading-normal">{detail}</p>
    </li>
  );
}
