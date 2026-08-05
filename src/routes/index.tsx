import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  ArrowUpRight,
  FileText,
  Download,
  AlertTriangle,
  ClipboardList,
  MessageSquareWarning,
  CheckCircle2,
  FileSearch,
  UserPlus,
  TrendingUp,
  Play,
  RotateCcw,
  Loader2,
  Check,
} from "lucide-react";
import { useDemo } from "@/lib/demo";
import { formatDateTime, relative } from "@/lib/format";
import { useState, useEffect } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard · SERA" },
      { name: "description", content: "What changed, what needs approval, what is at risk." },
    ],
  }),
  component: Dashboard,
});

const stages = [
  { key: "RECEIVED", label: "Received" },
  { key: "ANALYSING", label: "Analysing" },
  { key: "AWAITING_APPROVAL", label: "Awaiting Approval" },
  { key: "IMPLEMENTATION", label: "Implementation" },
  { key: "MONITORING", label: "Monitoring" },
] as const;

const SIMULATION_STEPS = [
  "New regulatory circular detected from SEBI source feeds",
  "PDF document ingested and structural layout metadata parsed",
  "Organizational scope checks completed (Applicable to Stockbrokers)",
  "Linguistic extraction of primary compliance obligations complete",
  "Delta mapping: Compared 24-month current with 12-month new requirement",
  "System recommendation generated for authenticated OTP verification mechanism",
  "Compliance review workspace configured and ready for human audit",
];

function Dashboard() {
  const {
    demoStage,
    setDemoStage,
    resetDemo,
    circulars,
    pipelineCounts,
    attentionCounts,
    implementationHealth,
    activity,
  } = useDemo();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simStep, setSimStep] = useState(0);

  const navigate = useNavigate();

  useEffect(() => {
    if (isSimulating) {
      if (simStep < SIMULATION_STEPS.length) {
        const timer = setTimeout(() => {
          setSimStep((prev) => prev + 1);
        }, 500); // 500ms per step
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => {
          setIsSimulating(false);
          setDialogOpen(false);
          setDemoStage("ANALYZED");
          toast.success("Regulatory Ingestion Complete", {
            description: "SEBI/HO/MIRSD/2026/104 has been loaded into your inbox.",
          });
          navigate({ to: "/inbox" });
        }, 600);
        return () => clearTimeout(timer);
      }
    }
  }, [isSimulating, simStep, setDemoStage, navigate]);

  const handleBeginWorkflow = () => {
    setIsSimulating(true);
    setSimStep(0);
    setDemoStage("DETECTED");
  };

  const handleReset = () => {
    resetDemo();
    setDialogOpen(false);
    toast.success("Demo Mode reset successfully.");
  };

  return (
    <AppShell>
      <PageHeader
        display
        title="Good Morning,"
        description="Devansh Narlawar  ·  3 logins today"
        actions={
          <>
            <Button
              onClick={() => setDialogOpen(true)}
              className="gap-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-medium shadow-md shadow-orange-500/10 cursor-pointer border-none"
            >
              <Play className="h-4 w-4 fill-current text-white" />
              {demoStage !== "OFF" ? "Demo Options" : "Start Demo Mode"}
            </Button>
            <Button className="gap-2">
              <FileText className="h-4 w-4" /> Upload Circular
            </Button>
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" /> Generate Report
            </Button>
          </>
        }
      />

      {/* Pipeline */}
      <section>
        <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          Regulatory Pipeline
        </div>
        <Card className="grid grid-cols-2 gap-0 divide-x divide-border rounded-2xl border-border p-0 md:grid-cols-5 bg-card">
          {stages.map((s, i) => {
            const count = pipelineCounts[s.key];
            const active =
              demoStage === "OFF"
                ? i === 0
                : (demoStage === "DETECTED" && s.key === "RECEIVED") ||
                  (demoStage === "ANALYZED" && s.key === "ANALYSING") ||
                  ((demoStage === "INTERPRETATION_APPROVED" || demoStage === "IMPACT_MAPPED") &&
                    s.key === "AWAITING_APPROVAL") ||
                  ((demoStage === "PLAN_APPROVED" ||
                    demoStage === "IMPLEMENTING" ||
                    demoStage === "EVIDENCE_REVIEW") &&
                    s.key === "IMPLEMENTATION") ||
                  (demoStage === "COMPLIANT" && s.key === "MONITORING");

            return (
              <div key={s.key} className="relative px-6 py-5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  {s.label}
                </div>
                <div
                  className={
                    "mt-2 text-3xl font-semibold tracking-tight transition-colors " +
                    (active ? "text-foreground font-bold" : "text-muted-foreground/70")
                  }
                >
                  {String(count).padStart(2, "0")}
                </div>
                {active && (
                  <span className="absolute inset-x-6 bottom-0 h-0.5 rounded-full bg-primary" />
                )}
              </div>
            );
          })}
        </Card>
      </section>

      {/* Attention + Health */}
      <section className="mt-10 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Attention Required
            </div>
            <Link to="/inbox" className="text-sm text-primary hover:underline">
              View all tasks
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <AttentionCard
              icon={<ClipboardList className="h-4 w-4" />}
              pill={<StatusPill tone="danger">URGENT</StatusPill>}
              count={attentionCounts.urgentApprovals}
              label="Pending Approvals"
            />
            <AttentionCard
              icon={<MessageSquareWarning className="h-4 w-4" />}
              count={attentionCounts.awaitingReview}
              label="Awaiting Review"
            />
            <AttentionCard
              icon={<AlertTriangle className="h-4 w-4" />}
              pill={<StatusPill tone="warning">RISK</StatusPill>}
              count={attentionCounts.implementationRisks}
              label="Implementation Risks"
            />
          </div>
        </div>

        <Card className="relative overflow-hidden rounded-2xl border-transparent bg-[oklch(0.22_0.06_145)] p-6 text-[oklch(0.95_0.02_90)]">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-[0.14]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.4) 1px, transparent 1px)",
              backgroundSize: "20px 20px",
            }}
          />
          <div className="relative">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">
              Implementation Health
            </div>
            <div className="mt-4 flex items-baseline justify-between">
              <div className="text-4xl font-semibold tracking-tight">
                {implementationHealth.score}%
              </div>
              <div className="flex items-center gap-1 text-sm text-emerald-300">
                <TrendingUp className="h-3.5 w-3.5" /> +{implementationHealth.delta}%
              </div>
            </div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/15">
              <div
                className="h-full rounded-full bg-emerald-400"
                style={{ width: `${implementationHealth.score}%` }}
              />
            </div>
            <div className="mt-6 text-xs text-white/70">Critical Compliance Exceptions</div>
            <div className="mt-1 text-2xl font-semibold">
              {String(implementationHealth.criticalExceptions).padStart(2, "0")}
            </div>
          </div>
        </Card>
      </section>

      {/* Circulars + Activity */}
      <section className="mt-10 grid gap-6 lg:grid-cols-[1fr_360px]">
        <Card className="overflow-hidden rounded-2xl p-0">
          <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Recent High-Priority Circulars
            </div>
            <div className="text-xs text-muted-foreground">Source: SEBI India</div>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                <th className="px-6 py-3">Reference No.</th>
                <th className="px-6 py-3">Circular Title</th>
                <th className="px-6 py-3">Risk</th>
                <th className="w-10 px-6 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {circulars.slice(0, 4).map((c) => (
                <tr
                  key={c.id}
                  onClick={() => {
                    if (c.id === "c-demo") {
                      if (demoStage === "DETECTED" || demoStage === "ANALYZED") {
                        navigate({ to: "/inbox" });
                      } else {
                        navigate({ to: "/workspace" });
                      }
                    } else {
                      navigate({ to: "/inbox" });
                    }
                  }}
                  className="group cursor-pointer border-t border-border transition-colors hover:bg-surface-2/60"
                >
                  <td className="px-6 py-4 font-medium text-foreground">
                    {c.reference}
                    {c.id === "c-demo" && (
                      <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-semibold text-amber-600 dark:text-amber-400">
                        DEMO
                      </span>
                    )}
                  </td>
                  <td className="max-w-[380px] truncate px-6 py-4 text-foreground/85">{c.title}</td>
                  <td className="px-6 py-4">
                    <StatusPill tone={riskTone(c.risk)} dot>
                      {c.risk}
                    </StatusPill>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">
                    <ArrowUpRight className="h-4 w-4 opacity-0 transition group-hover:opacity-100" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="rounded-2xl p-6">
          <div className="mb-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Recent Activity
          </div>
          <ol className="relative space-y-5 border-l border-border pl-5">
            {activity.map((a) => (
              <li key={a.id} className="relative">
                <span className="absolute -left-[26px] top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary">
                  {a.kind === "APPROVED" && <CheckCircle2 className="h-3 w-3" />}
                  {a.kind === "ANALYZED" && <FileSearch className="h-3 w-3" />}
                  {a.kind === "ASSIGNED" && <UserPlus className="h-3 w-3" />}
                  {a.kind === "FLAGGED" && <AlertTriangle className="h-3 w-3" />}
                </span>
                <div className="text-sm font-medium text-foreground">{a.title}</div>
                <p className="mt-0.5 text-xs text-muted-foreground">{a.detail}</p>
                <div className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground/80">
                  {formatDateTime(a.at)} · {relative(a.at)}
                </div>
              </li>
            ))}
          </ol>
        </Card>
      </section>

      {/* Demo Setup Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[540px] bg-background border-border">
          <DialogHeader>
            <div className="flex items-center gap-2 text-amber-500 font-semibold text-xs tracking-wider uppercase mb-1">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping" />
              Illustrative Demo Scenario
            </div>
            <DialogTitle className="text-2xl font-bold font-display leading-snug">
              SEBI Compliance Workflow Simulation
            </DialogTitle>
            <DialogDescription className="text-muted-foreground text-sm mt-1">
              Fictional Circular: <strong>SEBI/HO/MIRSD/2026/104</strong> <br />
              Subject: <em>Periodic Re-verification of Registered Client Mobile Numbers</em>
            </DialogDescription>
          </DialogHeader>

          {isSimulating ? (
            <div className="my-6 space-y-4">
              <div className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                Ingesting and Analyzing Circular...
              </div>
              <div className="space-y-2 rounded-xl border border-border bg-surface-2/50 p-4">
                {SIMULATION_STEPS.map((step, idx) => {
                  const isDone = simStep > idx;
                  const isActive = simStep === idx;
                  return (
                    <div
                      key={idx}
                      className={
                        "flex items-start gap-2.5 text-xs transition-opacity duration-300 " +
                        (isDone
                          ? "text-success font-medium"
                          : isActive
                            ? "text-foreground font-semibold"
                            : "text-muted-foreground/45")
                      }
                    >
                      <div className="mt-0.5">
                        {isDone ? (
                          <Check className="h-3.5 w-3.5 text-success stroke-[3px]" />
                        ) : isActive ? (
                          <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
                        ) : (
                          <div className="h-3.5 w-3.5 rounded-full border border-muted-foreground/20 flex items-center justify-center text-[8px]">
                            {idx + 1}
                          </div>
                        )}
                      </div>
                      <span>{step}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="my-4 text-sm text-muted-foreground leading-relaxed space-y-3">
              <p>
                This demo guides you through SERA’s regulatory action workflow using an
                illustrative SEBI scenario. In this scenario, SEBI reduces client mobile number
                re-verification cadence from <strong>24 months to 12 months</strong>, requiring
                OTP authentication and verified evidence storage.
              </p>
              <Card className="rounded-xl border-dashed border-border bg-surface-2 p-3 text-xs leading-normal">
                <strong>Simulated Stages:</strong> Detection &rarr; Applicability Analysis &rarr;
                Obligation Extraction &rarr; Impact Mapping &rarr; SOP Amendment &rarr; Task Execution
                &rarr; Evidence Review &rarr; Sealed Audit Trail.
              </Card>
              <div className="pt-2 text-xs font-medium text-amber-500/90 bg-amber-500/5 p-2 rounded-lg border border-amber-500/10 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
                <span>
                  <strong>Note:</strong> All data, AI results, and state transitions are fully
                  deterministic and mock-injected. No external network requests are executed.
                </span>
              </div>
            </div>
          )}

          <DialogFooter className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between sm:space-x-0 mt-4 border-t border-border pt-4">
            {demoStage !== "OFF" ? (
              <Button
                variant="destructive"
                onClick={handleReset}
                disabled={isSimulating}
                className="gap-2 cursor-pointer"
              >
                <RotateCcw className="h-4 w-4" /> Reset Demo
              </Button>
            ) : (
              <div className="text-xs text-muted-foreground flex items-center">
                Stage: Not Started
              </div>
            )}
            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => setDialogOpen(false)}
                disabled={isSimulating}
                className="cursor-pointer"
              >
                Cancel
              </Button>
              <Button
                onClick={handleBeginWorkflow}
                disabled={isSimulating}
                className="gap-2 bg-primary hover:bg-primary/95 text-primary-foreground cursor-pointer"
              >
                {isSimulating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Ingesting...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-current" /> Begin Workflow
                  </>
                )}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}

function AttentionCard({
  icon,
  pill,
  count,
  label,
}: {
  icon: React.ReactNode;
  pill?: React.ReactNode;
  count: number;
  label: string;
}) {
  return (
    <Card className="rounded-2xl p-5 bg-card border-border transition hover:border-primary/30 hover:shadow-sm">
      <div className="mb-8 flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
          {icon}
        </div>
        {pill}
      </div>
      <div className="text-3xl font-semibold tracking-tight text-foreground">
        {String(count).padStart(2, "0")}
      </div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </Card>
  );
}
