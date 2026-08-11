import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDemo } from "@/lib/demo";
import type { TaskStatus } from "@/lib/types";
import { Plus, MoreHorizontal, FileText, CheckCircle2, ChevronRight, ArrowRight, Loader2 } from "lucide-react";
import { formatDate } from "@/lib/format";
import { toast } from "sonner";
import { useWorkflow } from "@/hooks/useWorkflow";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";
import { AgentStatusBanner } from "@/components/sera/agent-status-banner";
import { SOPDiffCard } from "@/components/sera/sop-diff-card";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/implementation-plan")({
  head: () => ({ meta: [{ title: "Implementation Plan · SERA" }] }),
  component: PlanPage,
});

const LANES: TaskStatus[] = ["Todo", "In Progress", "Review", "Done"];

function PlanPage() {
  const { demoStage, setDemoStage, tasks, obligations, isDemoActive, workflowId } = useDemo();
  const navigate = useNavigate();
  const { data: workflowStatus } = useWorkflow(workflowId);
  
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sopDrafts, setSopDrafts] = useState<any[]>([]);
  const [agentTasks, setAgentTasks] = useState<any[]>([]);

  useEffect(() => {
    // If agent is done mapping, fetch its output
    if (workflowId && workflowStatus && workflowStatus.current_stage !== "impact_mapping" && workflowStatus.current_stage !== "planning") {
      api.getAgentOutput(workflowId, "sop_generation_agent")
        .then((output) => {
          if (output && output.sop_drafts) {
            setSopDrafts(output.sop_drafts);
          }
        })
        .catch(console.error);
        
      api.getAgentOutput(workflowId, "evidence_implementation_plan_agent")
        .then((output) => {
          if (output && output.tasks) {
            setAgentTasks(output.tasks);
          }
        })
        .catch(console.error);
    }
  }, [workflowId, workflowStatus]);

  const handleGate2 = async (decision: "approved" | "rejected") => {
    if (!workflowId) {
      if (decision === "approved") {
        setDemoStage("PLAN_APPROVED");
        toast.success("Execution Initiated", { description: "Tasks are being created in the tracker." });
        navigate({ to: "/implementation-tracker" });
      }
      return;
    }

    setIsSubmitting(true);
    try {
      await api.submitGate(workflowId, "gate_2", decision, comment || undefined);
      if (decision === "approved") {
        setDemoStage("PLAN_APPROVED");
        toast.success("Execution Initiated", { description: "Tasks are being created in the tracker." });
        navigate({ to: "/implementation-tracker" });
      } else {
        toast.info("Returned for Revision", { description: "The AI will revise the SOP drafts." });
        setComment("");
      }
    } catch (e) {
      toast.error("Failed to submit decision. Please retry.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isPlanning = workflowStatus?.current_stage === "planning" || workflowStatus?.current_stage === "impact_mapping";

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
              {isDemoActive && !workflowId && (
                <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  Demo Action Plan
                </span>
              )}
              {workflowStatus?.status === "executing" ? (
                <Button variant="outline" onClick={() => navigate({ to: "/implementation-tracker" })} className="gap-2 cursor-pointer">
                  Tracker View <ChevronRight className="h-4 w-4" />
                </Button>
              ) : null}
            </>
          }
        />

        {isPlanning && (
          <AgentStatusBanner
            icon={<Loader2 className="animate-spin" />}
            message="SERA is drafting SOP amendments and implementation tasks..."
            subtext="Generating specific, tailored tasks based on impact mapping."
          />
        )}
        
        {workflowStatus?.status === "executing" && (
           <AgentStatusBanner
            icon={<Loader2 className="animate-spin" />}
            message="Finalizing compliance actions..."
            subtext="Creating tasks, updating SOPs."
          />
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
          {/* Main Content Area */}
          <div className="space-y-6 relative">
             {isPlanning && (
               <div className="absolute inset-0 bg-background/50 backdrop-blur-[1px] rounded-2xl flex items-center justify-center z-10" />
             )}
             
            {/* Task list card */}
            <Card className="rounded-2xl p-6 bg-card border-border">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4 flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" /> Proposed Implementation Tasks ({agentTasks.length || 7})
              </h3>
              <div className="space-y-3.5">
                {agentTasks.length > 0 ? (
                  agentTasks.map((t, idx) => (
                    <TaskListItem key={idx} owner={t.assignee || "Unassigned"} title={t.title} desc={t.description || ""} due={t.due_date || "TBD"} />
                  ))
                ) : (
                  <>
                    <TaskListItem owner="IT Services" title="Change re-verification scheduler from 24 months to 12 months" desc="Update cron parameters in CRM client profile updater." due="15 Sep 2026" />
                    <TaskListItem owner="IT Services" title="Implement or configure authenticated OTP verification" desc="Integrate SMS gateway provider with Mobile Client app & login flow." due="20 Sep 2026" />
                    <TaskListItem owner="IT Services" title="Store verification timestamp and verification outcome" desc="Create database schema migrations for verification logging." due="22 Sep 2026" />
                    <TaskListItem owner="Operations" title="Update the Client Mobile Verification SOP" desc="Rewrite SOP-KYC-01 to reflect the 12-month re-verification mandate." due="01 Sep 2026" />
                    <TaskListItem owner="Customer Operations" title="Prepare customer reminder and escalation workflow" desc="Draft notification email templates and CRM agent call desk guides." due="25 Sep 2026" />
                    <TaskListItem owner="Compliance" title="Validate implementation against the approved obligation" desc="Human assessment of technical logs, QA reports and signed SOP." due="30 Sep 2026" />
                    <TaskListItem owner="QA Team" title="Test the end-to-end re-verification workflow" desc="Run regression tests on Mobile App OTP flow and database logs." due="28 Sep 2026" />
                  </>
                )}
              </div>
            </Card>

            {/* SOP Diff card */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-foreground pb-1">
                Proposed SOP Amendment Drafts
              </h3>
              {sopDrafts.length > 0 ? (
                sopDrafts.map((d, idx) => (
                  <SOPDiffCard
                    key={idx}
                    title={d.document_title || "New Document"}
                    departmentName={d.department || "Organization"}
                    isNewSop={!d.existing_content}
                    previousContent={d.existing_content}
                    newContent={d.proposed_content}
                  />
                ))
              ) : (
                <Card className="rounded-2xl p-6 bg-card border-border">
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
              )}
            </div>
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
            {(workflowStatus?.status === "pending_approval_2" || (!workflowId && demoStage === "IMPACT_MAPPED")) && (
              <Card className="rounded-2xl p-5 border-amber-500/20 bg-amber-500/5 flex flex-col justify-between min-h-[180px]">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Gate 2: Department Head Approval Required</h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Review the SOP amendments and implementation tasks above, then approve or return for revision.
                  </p>
                </div>
  
                <div className="mt-4 space-y-3">
                  <Textarea
                    placeholder="Optional comment (required if rejecting)"
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    className="text-xs"
                    disabled={isSubmitting}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleGate2("rejected")}
                      disabled={!comment || isSubmitting}
                      className="flex-1 text-xs cursor-pointer"
                    >
                      {isSubmitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                      Return for Revision
                    </Button>
                    <Button
                      onClick={() => handleGate2("approved")}
                      disabled={isSubmitting}
                      className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 text-xs cursor-pointer"
                    >
                      {isSubmitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                      Approve & Initiate
                    </Button>
                  </div>
                </div>
              </Card>
            )}
            
            {workflowStatus?.status === "executing" && (
                <Card className="rounded-2xl p-5 border-transparent bg-[oklch(0.22_0.06_145)] text-[oklch(0.95_0.02_90)] flex flex-col justify-between min-h-[180px]">
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
                </Card>
            )}
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
