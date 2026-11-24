import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useRef, useState } from "react";
import { CheckCircle2, FileCheck2, Fingerprint, ListChecks, Loader2, Paperclip, Play } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ErrorBox, Loading, RiskPill, Stat } from "@/components/sera/bits";
import { daysUntil, fmtDate, sera, useCirculars, useSeraMutation, useTasks, type TaskRow } from "@/lib/sera";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/implementation-tracker")({
  head: () => ({ meta: [{ title: "Implementation Tracker · SERA" }] }),
  component: Tracker,
});

const COLS: { key: TaskRow["status"]; label: string }[] = [
  { key: "Pending", label: "To do" },
  { key: "In Progress", label: "In progress" },
  { key: "Overdue", label: "Overdue" },
  { key: "Completed", label: "Done" },
];

function Tracker() {
  const { data: tasks, error, isLoading } = useTasks();
  const { data: circulars } = useCirculars();
  const [wfFilter, setWfFilter] = useState<string>("all");
  const [dept, setDept] = useState<string>("all");
  const [evTask, setEvTask] = useState<TaskRow | null>(null);
  const patch = useSeraMutation((a: { id: string; status: string }) => sera.patchTask(a.id, { status: a.status }));

  const wfTitle = Object.fromEntries((circulars ?? []).map((c) => [c.workflow_id, c.title]));
  const depts = useMemo(() => Array.from(new Set((tasks ?? []).map((t) => t.department ?? "-"))).sort(), [tasks]);
  const rows = (tasks ?? []).filter((t) => (wfFilter === "all" || t.workflow_id === wfFilter) && (dept === "all" || t.department === dept));
  const done = rows.filter((t) => t.status === "Completed").length;
  const overdue = rows.filter((t) => t.status === "Overdue").length;
  const evidenced = rows.filter((t) => t.evidence_files.length).length;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Execution"
        title="Implementation Tracker"
        description="Every approved task with its owner, deadline and evidence. Uploaded evidence is SHA-256 fingerprinted and written to the audit chain."
      />
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {tasks && tasks.length === 0 && (
        <EmptyState icon={<ListChecks className="h-5 w-5" />} title="No live tasks yet" description="Tasks appear here after a plan is approved at Gate 2." action={<Button asChild><Link to="/implementation-plan">Implementation plan</Link></Button>} />
      )}
      {tasks && tasks.length > 0 && (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-4">
            <Stat label="Tasks" value={rows.length} />
            <Stat label="Completed" value={`${done}/${rows.length}`} tone="success" hint={`${rows.length ? Math.round((100 * done) / rows.length) : 0}% complete`} />
            <Stat label="Overdue" value={overdue} tone={overdue ? "danger" : undefined} />
            <Stat label="With evidence" value={evidenced} hint="hash-verified files" />
          </div>
          <div className="mb-4 flex flex-wrap gap-3">
            <select value={wfFilter} onChange={(e) => setWfFilter(e.target.value)} className="h-9 rounded-md border border-border bg-surface px-3 text-sm">
              <option value="all">All circulars</option>
              {Array.from(new Set(tasks.map((t) => t.workflow_id))).map((w) => <option key={w} value={w}>{(wfTitle[w] ?? w).slice(0, 70)}</option>)}
            </select>
            <select value={dept} onChange={(e) => setDept(e.target.value)} className="h-9 rounded-md border border-border bg-surface px-3 text-sm">
              <option value="all">All departments</option>
              {depts.map((d) => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div className="grid gap-4 lg:grid-cols-4">
            {COLS.map((col) => {
              const list = rows.filter((t) => (col.key === "Pending" ? t.status === "Pending" || t.status === "Blocked" : t.status === col.key));
              return (
                <div key={col.key} className="rounded-2xl bg-surface-2/50 p-3">
                  <div className="mb-3 flex items-center justify-between px-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                    {col.label}<span className="rounded-full bg-background px-2 py-0.5">{list.length}</span>
                  </div>
                  <div className="space-y-3">
                    {list.map((t) => {
                      const d = daysUntil(t.due_date);
                      return (
                        <Card key={t.id} className={cn("rounded-xl p-4", t.status === "Overdue" && "border-destructive/40")}>
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono text-[10px] text-muted-foreground">{t.obligation_code} · {t.phase}</span>
                            <RiskPill risk={t.priority} />
                          </div>
                          <div className="mt-1.5 text-[13px] font-semibold leading-snug">{t.title}</div>
                          <div className="mt-1 text-xs text-muted-foreground">{t.department}</div>
                          <div className="mt-2 flex items-center justify-between text-xs">
                            <span className={cn(d !== null && d < 0 && t.status !== "Completed" && "font-semibold text-destructive")}>Due {fmtDate(t.due_date)}</span>
                            {t.evidence_files.length > 0 && <span className="inline-flex items-center gap-1 text-success"><Fingerprint className="h-3 w-3" />{t.evidence_files.length}</span>}
                          </div>
                          {t.status !== "Completed" && (
                            <div className="mt-3 flex gap-2">
                              {t.raw_status === "Pending" && (
                                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => patch.mutate({ id: t.id, status: "In Progress" }, { onError: (e) => toast.error(e.message) })}>
                                  <Play className="mr-1 h-3 w-3" /> Start
                                </Button>
                              )}
                              <Button size="sm" className="h-7 text-xs" onClick={() => setEvTask(t)}>
                                <Paperclip className="mr-1 h-3 w-3" /> {t.evidence_requirement ? "Submit evidence" : "Complete"}
                              </Button>
                            </div>
                          )}
                          {t.status === "Completed" && (
                            <button onClick={() => setEvTask(t)} className="mt-2 inline-flex items-center gap-1 text-xs text-success hover:underline">
                              <CheckCircle2 className="h-3 w-3" /> Completed {t.completed_at ? fmtDate(t.completed_at) : ""} · view evidence
                            </button>
                          )}
                        </Card>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
      {evTask && <EvidenceDialog task={evTask} onClose={() => setEvTask(null)} />}
    </AppShell>
  );
}

function EvidenceDialog({ task, onClose }: { task: TaskRow; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [note, setNote] = useState(task.evidence_note ?? "");
  const [complete, setComplete] = useState(true);
  const ref = useRef<HTMLInputElement>(null);
  const upload = useSeraMutation(() => sera.evidence(task.id, file!, note, complete));
  const finish = useSeraMutation(() => sera.patchTask(task.id, { status: "Completed", note }));
  const readOnly = task.status === "Completed";
  const busy = upload.isPending || finish.isPending;

  const submit = () => {
    const p = file ? upload.mutateAsync(undefined) : finish.mutateAsync(undefined);
    p.then(() => { toast.success(file ? "Evidence fingerprinted and recorded" : "Task completed"); onClose(); }).catch((e) => toast.error(e.message));
  };

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="leading-snug">{task.title}</DialogTitle>
          <DialogDescription>{task.description}</DialogDescription>
        </DialogHeader>
        {task.evidence_requirement && (
          <div className="rounded-lg bg-surface-2 p-3 text-[13px]"><span className="font-semibold">Required evidence: </span>{task.evidence_requirement}</div>
        )}
        {task.evidence_files.length > 0 && (
          <div className="space-y-2">
            {task.evidence_files.map((f) => (
              <a key={f.sha256 + f.name} href={sera.evidenceUrl(task.id, f.name)} target="_blank" rel="noreferrer" className="flex items-center gap-3 rounded-lg border border-border p-2.5 text-[13px] hover:border-primary/40">
                <FileCheck2 className="h-4 w-4 text-success" />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">{f.name}</div>
                  <div className="truncate font-mono text-[10px] text-muted-foreground">sha256 {f.sha256.slice(0, 24)}… · {(f.size / 1024).toFixed(1)} KB · {f.by}</div>
                </div>
                <StatusPill tone="success">verified</StatusPill>
              </a>
            ))}
          </div>
        )}
        {!readOnly && (
          <>
            <div onClick={() => ref.current?.click()} className="cursor-pointer rounded-lg border border-dashed border-border p-4 text-center text-sm text-muted-foreground hover:border-primary/50">
              {file ? <span className="text-foreground">{file.name}</span> : "Click to attach an evidence file (PDF, screenshot, export…)"}
              <input ref={ref} type="file" hidden onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </div>
            <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Completion note (what was done, where it is recorded)" />
            {file && (
              <label className="flex items-center gap-2 text-sm"><Checkbox checked={complete} onCheckedChange={(v) => setComplete(!!v)} /> Mark task as completed</label>
            )}
          </>
        )}
        {readOnly && task.evidence_note && <div className="text-sm"><span className="text-muted-foreground">Note: </span>{task.evidence_note}</div>}
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Close</Button>
          {!readOnly && (
            <Button disabled={busy || (!file && !!task.evidence_requirement && task.evidence_files.length === 0 && !note.trim())} onClick={submit}>
              {busy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
              {file ? "Upload evidence" : "Mark complete"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
