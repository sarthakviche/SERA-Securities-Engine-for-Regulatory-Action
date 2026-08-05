import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDemo } from "@/lib/demo";
import type { TaskStatus } from "@/lib/types";
import { Plus, MoreHorizontal, FileText, CheckCircle2, ChevronRight, ArrowRight } from "lucide-react";
import { formatDate } from "@/lib/format";
import { toast } from "sonner";

export const Route = createFileRoute("/implementation-plan")({
  head: () => ({ meta: [{ title: "Implementation Plan · SERA" }] }),
  component: PlanPage,
});

const LANES: TaskStatus[] = ["Todo", "In Progress", "Review", "Done"];

function PlanPage() {
  const { demoStage, setDemoStage, tasks, obligations, isDemoActive } = useDemo();
  const navigate = useNavigate();

  const handleApprovePlan = () => {
    setDemoStage("PLAN_APPROVED");
    toast.success("Implementation Plan Approved", {
      description: "Live tasks initialized and assigned. Redirecting to tracker...",
    });
    navigate({ to: "/implementation-tracker" });
  };

  // Render rich demo plan if demo mode is active
  if (isDemoActive) {
    return (
      <AppShell>
        <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
          <Link to="/" className="hover:text-foreground">Workspace</Link>
          <span>/</span>
          <span className="text-foreground">Implementation Plan</span>
        </div>

        <PageHeader
          title="Implementation Plan"
          description="Fictional Circular SEBI/HO/MIRSD/2026/104: Core Action Plan & SOP Amendment Draft"
          actions={
            <>
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Action Plan
              </span>
              {demoStage === "IMPACT_MAPPED" ? (
                <Button onClick={handleApprovePlan} className="gap-2 bg-primary hover:bg-primary/95 text-primary-foreground cursor-pointer">
                  <CheckCircle2 className="h-4 w-4" /> Approve Plan
                </Button>
              ) : (
                <Button variant="outline" onClick={() => navigate({ to: "/implementation-tracker" })} className="gap-2 cursor-pointer">
                  Tracker View <ChevronRight className="h-4 w-4" />
                </Button>
              )}
            </>
          }
        />

        <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
          {/* Main Content Area */}
          <div className="space-y-6">
            {/* Task list card */}
            <Card className="rounded-2xl p-6 bg-card border-border">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4 flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" /> Proposed Implementation Tasks (7)
              </h3>
              <div className="space-y-3.5">
                <TaskListItem owner="IT Services" title="Change re-verification scheduler from 24 months to 12 months" desc="Update cron parameters in CRM client profile updater." due="15 Sep 2026" />
                <TaskListItem owner="IT Services" title="Implement or configure authenticated OTP verification" desc="Integrate SMS gateway provider with Mobile Client app & login flow." due="20 Sep 2026" />
                <TaskListItem owner="IT Services" title="Store verification timestamp and verification outcome" desc="Create database schema migrations for verification logging." due="22 Sep 2026" />
                <TaskListItem owner="Operations" title="Update the Client Mobile Verification SOP" desc="Rewrite SOP-KYC-01 to reflect the 12-month re-verification mandate." due="01 Sep 2026" />
                <TaskListItem owner="Customer Operations" title="Prepare customer reminder and escalation workflow" desc="Draft notification email templates and CRM agent call desk guides." due="25 Sep 2026" />
                <TaskListItem owner="Compliance" title="Validate implementation against the approved obligation" desc="Human assessment of technical logs, QA reports and signed SOP." due="30 Sep 2026" />
                <TaskListItem owner="QA Team" title="Test the end-to-end re-verification workflow" desc="Run regression tests on Mobile App OTP flow and database logs." due="28 Sep 2026" />
              </div>
            </Card>

            {/* SOP Diff card */}
            <Card className="rounded-2xl p-6 bg-card border-border">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4">
                Proposed SOP Amendment Diff (SOP-KYC-01)
              </h3>
              <div className="rounded-xl border border-border bg-surface font-mono text-[11px] leading-relaxed overflow-hidden">
                <div className="bg-surface-2 px-4 py-2 border-b border-border text-muted-foreground flex justify-between">
                  <span>SOP-KYC-01 Section 4.2</span>
                  <span>Unified Diff</span>
                </div>
                <div className="p-4 space-y-1.5">
                  <div className="text-muted-foreground">@@ -18,4 +18,4 @@</div>
                  <div className="bg-destructive/10 text-destructive px-2 py-1 rounded flex items-start gap-1">
                    <span className="select-none font-bold">-</span>
                    <span>“Registered mobile numbers shall be periodically re-verified every 24 months.”</span>
                  </div>
                  <div className="bg-success/10 text-success px-2 py-1 rounded flex items-start gap-1">
                    <span className="select-none font-bold">+</span>
                    <span>“Registered mobile numbers shall be periodically re-verified every 12 months through the approved authenticated verification workflow.”</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar Area */}
          <div className="space-y-6">
            {/* Evidence Requirements */}
            <Card className="rounded-2xl p-5 bg-card border-border">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4">
                Required Evidence Plan
              </h3>
              <ul className="space-y-3 text-xs leading-normal">
                <EvidenceItem title="Approved SOP Document" desc="Signed SOP-KYC-01 v2.0 PDF" />
                <EvidenceItem title="Deployment Record" desc="Production build config change log" />
                <EvidenceItem title="QA Test Report" desc="End-to-end OTP workflow run record" />
                <EvidenceItem title="Sample Verification Logs" desc="Anonymized db verification log entries" />
                <EvidenceItem title="System Configuration Evidence" desc="Mobile app SMS gateway configuration parameters" />
                <EvidenceItem title="Compliance Sign-off" desc="Human audit attestation checklist sealed" />
              </ul>
            </Card>

            {/* Approval CTA Card */}
            <Card className="rounded-2xl p-5 border-transparent bg-[oklch(0.22_0.06_145)] text-[oklch(0.95_0.02_90)] flex flex-col justify-between min-h-[180px]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-white/70">
                  Plan Authorization
                </h4>
                <p className="mt-2 text-xs text-white/80 leading-relaxed">
                  Approving this implementation plan locks the SOP amendment and instantiates the 7 tasks in the live tracker.
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/10">
                {demoStage === "IMPACT_MAPPED" ? (
                  <Button
                    onClick={handleApprovePlan}
                    className="w-full gap-2 bg-white text-emerald-950 hover:bg-white/90 border-none font-semibold cursor-pointer text-xs"
                  >
                    Approve Implementation Plan <ArrowRight className="h-4 w-4" />
                  </Button>
                ) : (
                  <div className="space-y-2">
                    <div className="text-center text-xs font-bold text-emerald-300 flex items-center justify-center gap-1.5 py-1.5 bg-white/10 rounded-lg">
                      <CheckCircle2 className="h-4 w-4" /> Plan Approved
                    </div>
                    <Button
                      variant="ghost"
                      onClick={() => navigate({ to: "/implementation-tracker" })}
                      className="w-full text-white/80 hover:text-white hover:bg-white/10 text-xs font-medium cursor-pointer"
                    >
                      View Live Tracker Tasks
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      </AppShell>
    );
  }

  // Kanban view (default baseline mockup)
  return (
    <AppShell>
      <PageHeader
        title="Implementation Plan"
        description="Owner-assigned task lanes derived from every obligation."
        actions={
          <Button className="gap-2">
            <Plus className="h-4 w-4" /> Add Task
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {LANES.map((lane) => {
          const laneTasks = tasks.filter((t) => t.status === lane);
          return (
            <div key={lane} className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <span
                    className={
                      "h-2 w-2 rounded-full " +
                      (lane === "Todo"
                        ? "bg-muted-foreground"
                        : lane === "In Progress"
                          ? "bg-info"
                          : lane === "Review"
                            ? "bg-warning"
                            : "bg-success")
                    }
                  />
                  {lane}
                </div>
                <span className="text-xs text-muted-foreground">{laneTasks.length}</span>
              </div>
              <div className="space-y-3">
                {laneTasks.map((t) => {
                  const ob = obligations.find((o) => o.id === t.obligationId);
                  return (
                    <Card
                      key={t.id}
                      className="cursor-grab rounded-xl p-4 shadow-none transition hover:border-primary/40 hover:shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <StatusPill tone="brand">{ob?.code ?? "OB"}</StatusPill>
                        <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="mt-3 text-sm font-medium leading-snug">{t.title}</div>
                      <div className="mt-3 h-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${t.progress}%` }}
                        />
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                        <span>{t.assignee}</span>
                        <span>{formatDate(t.dueDate)}</span>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </AppShell>
  );
}

function TaskListItem({ owner, title, desc, due }: { owner: string; title: string; desc: string; due: string }) {
  return (
    <div className="border border-border rounded-xl p-3 flex gap-3 items-start hover:border-primary/30 transition bg-background">
      <div className="shrink-0 font-mono text-[9px] font-bold bg-muted text-muted-foreground px-2 py-0.5 rounded uppercase mt-0.5">
        {owner}
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-foreground leading-normal">{title}</div>
        <p className="text-[10px] text-muted-foreground mt-0.5">{desc}</p>
        <span className="text-[9px] text-muted-foreground/80 block mt-1.5">Deadline: {due}</span>
      </div>
    </div>
  );
}

function EvidenceItem({ title, desc }: { title: string; desc: string }) {
  return (
    <li className="flex gap-2.5 items-start">
      <div className="h-4 w-4 rounded-full bg-primary/10 border border-primary/25 text-primary flex items-center justify-center shrink-0 mt-0.5 text-[8px] font-bold">
        &bull;
      </div>
      <div>
        <div className="font-semibold text-foreground">{title}</div>
        <div className="text-[10px] text-muted-foreground">{desc}</div>
      </div>
    </li>
  );
}
