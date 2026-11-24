import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Check, FileText, Loader2, RotateCcw, ShieldCheck, Workflow } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorBox, Loading, NoCircular, RiskPill, SectionTitle, StageStepper, WorkflowPicker } from "@/components/sera/bits";
import { fmtDate, sera, useActiveWorkflow, useSeraMutation, useWorkflow } from "@/lib/sera";

export const Route = createFileRoute("/implementation-plan")({
  head: () => ({ meta: [{ title: "Implementation Plan · SERA" }] }),
  component: Plan,
});

function Plan() {
  const [wfId, setWf, circulars] = useActiveWorkflow();
  const { data: wf, error, isLoading } = useWorkflow(wfId);
  const [comment, setComment] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const gate = useSeraMutation((d: "approved" | "rejected") => sera.gate(wfId!, "gate_2", d, comment || undefined));
  const pending = wf?.status === "pending_approval_2";

  return (
    <AppShell>
      <PageHeader
        eyebrow="Planning · Gate 2"
        title="Implementation Plan"
        description="SOP amendments and a phased, owner-assigned task plan generated from the approved obligations. Department heads approve before tasks go live."
        actions={<WorkflowPicker value={wfId} onChange={setWf} circulars={circulars} />}
      />
      {!wfId && circulars && <NoCircular />}
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {wf && !wf.plan && (
        <EmptyState icon={<Workflow className="h-5 w-5" />} title="No plan yet" description="Approve the interpretation at Gate 1 to generate the plan." action={<Button asChild><Link to="/workspace">Go to Workspace</Link></Button>} />
      )}
      {wf && wf.plan && (
        <>
          <Card className="mb-6 rounded-2xl p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="font-semibold">{wf.circular.title}</div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  Plan starts {fmtDate(wf.plan.start_date)} · {wf.plan.tasks.length} tasks · {wf.sops?.length ?? 0} SOP changes
                  {wf.plan_revision > 0 && ` · revision ${wf.plan_revision}`}
                </div>
              </div>
              <StageStepper status={wf.status} />
            </div>
            {wf.plan.feedback_applied && (
              <div className="mt-3 rounded-lg bg-info/10 px-3 py-2 text-[13px] text-info">
                <RotateCcw className="mr-1 inline h-3.5 w-3.5" /> Regenerated after reviewer feedback: "{wf.plan.feedback_applied}"
              </div>
            )}
          </Card>

          <Tabs defaultValue="plan">
            <TabsList>
              <TabsTrigger value="plan">Task plan</TabsTrigger>
              <TabsTrigger value="sops">SOP amendments ({wf.sops?.length ?? 0})</TabsTrigger>
            </TabsList>
            <TabsContent value="plan" className="mt-4 space-y-6">
              {wf.plan.phases.map((ph) => {
                const tasks = wf.plan!.tasks.filter((t) => t.phase === ph.name);
                if (!tasks.length) return null;
                return (
                  <div key={ph.name}>
                    <SectionTitle right={<span className="text-xs text-muted-foreground">{ph.description}</span>}>{ph.name} · {tasks.length}</SectionTitle>
                    <Card className="overflow-hidden rounded-2xl p-0">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                            <th className="px-5 py-2.5">Task</th><th className="px-3 py-2.5">Owner</th><th className="px-3 py-2.5">Due</th><th className="px-3 py-2.5">Priority</th><th className="px-5 py-2.5">Evidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tasks.map((t, i) => (
                            <tr key={i} className="border-t border-border align-top">
                              <td className="px-5 py-3"><div className="font-medium">{t.title}</div><div className="font-mono text-[10px] text-muted-foreground">{t.obligation_code}</div></td>
                              <td className="px-3 py-3">{t.department}</td>
                              <td className="whitespace-nowrap px-3 py-3">{fmtDate(t.due_date)}</td>
                              <td className="px-3 py-3"><RiskPill risk={t.priority} /></td>
                              <td className="px-5 py-3 text-muted-foreground">{t.evidence_requirement ?? "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </Card>
                  </div>
                );
              })}
            </TabsContent>
            <TabsContent value="sops" className="mt-4 space-y-4">
              {(wf.sops ?? []).map((s, i) => (
                <Card key={i} className="rounded-2xl p-5">
                  <div className="flex items-center gap-3 border-b border-border pb-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-2"><FileText className="h-4 w-4 text-muted-foreground" /></span>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold">{s.sop_title}</div>
                      <div className="text-[11px] text-muted-foreground">{s.citation} · {s.obligation_code}</div>
                    </div>
                    <StatusPill tone={s.change_type === "Add" ? "brand" : "warning"}>{s.change_type === "Add" ? "New section" : "Amendment"}</StatusPill>
                  </div>
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <div className="rounded-xl border border-border bg-surface-2 p-4">
                      <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Current</div>
                      <div className="text-xs italic text-muted-foreground">{s.current_text}</div>
                    </div>
                    <div className="rounded-xl border border-primary/25 bg-primary/5 p-4">
                      <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-primary">Proposed</div>
                      <div className="whitespace-pre-line text-xs leading-relaxed">{s.proposed_text}</div>
                    </div>
                  </div>
                </Card>
              ))}
            </TabsContent>
          </Tabs>

          {pending ? (
            <Card className="sticky bottom-4 z-20 mt-6 rounded-2xl border-primary/30 p-5 shadow-xl">
              <div className="flex flex-wrap items-center gap-4">
                <ShieldCheck className="h-5 w-5 text-primary" />
                <div className="min-w-0 flex-1 text-sm">
                  <div className="font-semibold">Gate 2: approve the SOPs and task plan?</div>
                  <div className="text-muted-foreground">Approval creates {wf.plan.tasks.length} tracked tasks with owners, due dates and evidence requirements. Rejecting regenerates the plan using your feedback.</div>
                </div>
                {rejecting ? (
                  <div className="flex w-full items-end gap-2 md:w-auto">
                    <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Feedback for the revised plan" className="min-h-[40px] md:w-80" />
                    <Button variant="destructive" disabled={!comment.trim() || gate.isPending} onClick={() => gate.mutate("rejected", { onSuccess: () => { toast("Plan regenerated with your feedback"); setRejecting(false); setComment(""); }, onError: (e) => toast.error(e.message) })}>Request changes</Button>
                    <Button variant="ghost" onClick={() => setRejecting(false)}>Cancel</Button>
                  </div>
                ) : (
                  <>
                    <Button variant="outline" onClick={() => setRejecting(true)}>Request changes</Button>
                    <Button disabled={gate.isPending} onClick={() => gate.mutate("approved", { onSuccess: () => toast.success("Plan approved. Tasks are live in the tracker."), onError: (e) => toast.error(e.message) })}>
                      {gate.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Check className="mr-1.5 h-4 w-4" />} Approve plan
                    </Button>
                  </>
                )}
              </div>
            </Card>
          ) : (
            wf.approvals.gate_2?.decision === "approved" && (
              <Card className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl p-5 text-sm">
                <div><StatusPill tone="success">Gate 2 approved</StatusPill><span className="ml-2 text-muted-foreground">by {wf.approvals.gate_2.by} · {fmtDate(wf.approvals.gate_2.at)}</span></div>
                <Button asChild size="sm"><Link to="/implementation-tracker">Track implementation <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link></Button>
              </Card>
            )
          )}
        </>
      )}
    </AppShell>
  );
}
