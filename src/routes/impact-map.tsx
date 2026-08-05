import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Lock, Loader2, Plus, Download, ArrowRight, Network } from "lucide-react";
import { useDemo } from "@/lib/demo";
import { toast } from "sonner";

export const Route = createFileRoute("/impact-map")({
  head: () => ({ meta: [{ title: "Impact Map · SERA" }] }),
  component: ImpactMap,
});

const COLUMNS = [
  { key: "clause", label: "Clause" },
  { key: "obligation", label: "Obligation" },
  { key: "process", label: "Process" },
  { key: "system", label: "Systems" },
  { key: "department", label: "Department" },
  { key: "owner", label: "Owner" },
  { key: "evidence", label: "Evidence" },
];

// Fictional SEBI scenario nodes
const demoNodes = [
  { col: "clause", code: "CLAUSE 2", title: "12M Re-verification Mandate", tone: "brand" as const, highlight: true },
  { col: "obligation", code: "OB-MIRSD-104", title: "Periodic Mobile Re-verification", tone: "neutral" as const },
  { col: "process", code: "PROC-KYC-01", title: "Periodic KYC Profile Maintenance", tone: "neutral" as const },
  { col: "system", code: "SYS-CRM", title: "CRM Client Records", tone: "neutral" as const },
  { col: "system", code: "SYS-APP", title: "Mobile Client App", tone: "neutral" as const },
  { col: "system", code: "SYS-SMS", title: "SMS Gateway Service", tone: "neutral" as const },
  { col: "department", code: "", title: "IT Infrastructure", tone: "neutral" as const },
  { col: "department", code: "", title: "Operations Queue", tone: "neutral" as const },
  { col: "owner", code: "", title: "Sarah Miller (Ops)", tone: "neutral" as const },
  { col: "owner", code: "", title: "IT Admin Team (IT)", tone: "neutral" as const },
  { col: "evidence", code: "DOC-SOP-104", title: "Client Verification SOP v2.0", tone: "neutral" as const },
  { col: "evidence", code: "LOG-OTP", title: "SMS OTP Verification Logs", tone: "neutral" as const },
];

// Baseline DORA nodes
const defaultNodes = [
  { col: "clause", code: "ART 17.1", title: "Risk Assessment Strategy", tone: "brand" as const, highlight: true },
  { col: "obligation", code: "OB-042", title: "Annual Third-Party Audit", tone: "neutral" as const },
  { col: "obligation", code: "OB-043", title: "Contractual Clause Rev.", tone: "neutral" as const },
  { col: "process", code: "PROC-VND-01", title: "Vendor Onboarding", tone: "neutral" as const },
  { col: "system", code: "SYS-GRC", title: "Archer GRC Platform", tone: "neutral" as const },
  { col: "system", code: "SYS-ERP", title: "SAP Vendor Portal", tone: "neutral" as const },
  { col: "department", code: "", title: "Procurement", tone: "neutral" as const },
  { col: "department", code: "", title: "Risk & Compliance", tone: "neutral" as const },
  { col: "owner", code: "", title: "Sarah Jenkins", tone: "neutral" as const },
  { col: "owner", code: "", title: "Mark Thorogood", tone: "neutral" as const },
  { col: "evidence", code: "DOC-AUDIT-23", title: "Annual Report 2023", tone: "neutral" as const },
];

function ImpactMap() {
  const { demoStage, setDemoStage, isDemoActive } = useDemo();
  const navigate = useNavigate();

  const handleConfirmMapping = () => {
    setDemoStage("IMPACT_MAPPED");
    toast.success("Impact Mapping Confirmed", {
      description: "Propagation relationships mapped. Proceeding to Implementation Plan.",
    });
    navigate({ to: "/implementation-plan" });
  };

  const currentNodes = isDemoActive ? demoNodes : defaultNodes;

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
            {isDemoActive && (
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

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Node graph mapping visualization */}
        <Card className="overflow-hidden rounded-2xl p-6 bg-card border-border">
          <div
            className="relative rounded-xl border border-dashed border-border bg-surface-2/40 p-6 overflow-x-auto min-w-[800px]"
            style={{
              backgroundImage:
                "radial-gradient(oklch(from var(--color-border) l c h / 60%) 1px, transparent 1px)",
              backgroundSize: "16px 16px",
            }}
          >
            <div className="grid grid-cols-7 gap-4 text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground select-none pb-2 border-b border-border mb-4">
              {COLUMNS.map((c) => (
                <div key={c.key}>{c.label}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-4 relative">
              {COLUMNS.map((c) => (
                <div key={c.key} className="flex flex-col gap-3 z-10">
                  {currentNodes
                    .filter((n) => n.col === c.key)
                    .map((n, i) => (
                      <div
                        key={i}
                        className={
                          "rounded-lg border bg-card p-2.5 text-xs shadow-sm transition " +
                          (n.highlight
                            ? "border-primary ring-2 ring-primary/20"
                            : "border-border hover:border-primary/40 hover:shadow-sm")
                        }
                      >
                        {n.code && (
                          <div className="mb-1 text-[9px] font-bold text-muted-foreground font-mono">
                            {n.code}
                          </div>
                        )}
                        <div className="font-semibold leading-tight text-foreground">{n.title}</div>
                      </div>
                    ))}
                </div>
              ))}
            </div>
          </div>
        </Card>

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
                <span className="font-semibold text-primary">100%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-primary" style={{ width: "100%" }} />
              </div>
              <div className="mt-1 text-[10px] text-muted-foreground">All nodes mapped & verified</div>
            </div>
          </Card>

          <Card className="rounded-2xl p-5 bg-card border-border">
            <div className="text-base font-semibold text-foreground border-b border-border pb-3 mb-3">
              Propagation Rationale
            </div>
            {isDemoActive ? (
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
                {demoStage === "INTERPRETATION_APPROVED" ? (
                  <Button
                    onClick={handleConfirmMapping}
                    className="w-full gap-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-none cursor-pointer text-xs"
                  >
                    Confirm Impact Mapping <ArrowRight className="h-3.5 w-3.5" />
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
