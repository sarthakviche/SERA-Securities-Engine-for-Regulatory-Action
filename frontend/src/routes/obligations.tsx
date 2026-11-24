import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { ClipboardCheck, Search } from "lucide-react";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Card } from "@/components/ui/card";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Citation, ErrorBox, Loading, RiskPill } from "@/components/sera/bits";
import { daysUntil, fmtDate, useObligations, type ObligationRow } from "@/lib/sera";

export const Route = createFileRoute("/obligations")({
  head: () => ({ meta: [{ title: "Obligations · SERA" }] }),
  component: Obligations,
});

const STATUS: Record<ObligationRow["status"], { label: string; tone: "neutral" | "info" | "success" | "warning" }> = {
  pending: { label: "Awaiting Gate 1", tone: "neutral" },
  active: { label: "In implementation", tone: "info" },
  completed: { label: "Compliant", tone: "success" },
  waived: { label: "Waived", tone: "neutral" },
};

function Obligations() {
  const [showExcluded, setShowExcluded] = useState(false);
  const { data, error, isLoading } = useObligations(showExcluded);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");
  const [sel, setSel] = useState<ObligationRow | null>(null);
  const cats = useMemo(() => Array.from(new Set((data ?? []).map((o) => o.category))).sort(), [data]);
  const rows = (data ?? []).filter(
    (o) => (cat === "all" || o.category === cat) && (!q || `${o.title} ${o.code} ${o.source_text} ${o.circular_ref}`.toLowerCase().includes(q.toLowerCase())),
  );

  return (
    <AppShell>
      <PageHeader eyebrow="Obligation register" title="Obligations" description="Every requirement SERA extracted across all circulars, each linked to its source clause, owner, deadline and progress." />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative w-80">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search obligations or source text" className="h-9 w-full rounded-full border border-border bg-surface pl-8 pr-3 text-sm outline-none focus:border-primary" />
        </div>
        <select value={cat} onChange={(e) => setCat(e.target.value)} className="h-9 rounded-md border border-border bg-surface px-3 text-sm">
          <option value="all">All categories</option>
          {cats.map((c) => <option key={c}>{c}</option>)}
        </select>
        <label className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
          <input type="checkbox" checked={showExcluded} onChange={(e) => setShowExcluded(e.target.checked)} /> Show excluded / not applicable
        </label>
      </div>
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {data && rows.length === 0 && <EmptyState icon={<ClipboardCheck className="h-5 w-5" />} title="No obligations yet" description="Analyse a circular from the Inbox to populate the register." />}
      {rows.length > 0 && (
        <Card className="overflow-hidden rounded-2xl p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                <th className="px-5 py-3">Obligation</th><th className="px-3 py-3">Owner</th><th className="px-3 py-3">Deadline</th><th className="px-3 py-3">Risk</th><th className="px-3 py-3">Status</th><th className="px-5 py-3">Progress</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => {
                const d = daysUntil(o.due_date);
                return (
                  <tr key={o.id} onClick={() => setSel(o)} className="cursor-pointer border-t border-border align-top hover:bg-surface-2/40">
                    <td className="max-w-[460px] px-5 py-3.5">
                      <div className="font-mono text-[10px] text-muted-foreground">{o.code} · {o.clause_ref} · {o.circular_ref}</div>
                      <div className="mt-0.5 font-medium leading-snug">{o.title}</div>
                    </td>
                    <td className="px-3 py-3.5">{o.department ?? <span className="text-muted-foreground">Unassigned</span>}</td>
                    <td className="whitespace-nowrap px-3 py-3.5">
                      {o.due_date ? fmtDate(o.due_date) : <span className="text-muted-foreground">Not stated</span>}
                      {d !== null && d < 0 && o.status !== "completed" && <div className="text-[11px] font-semibold text-destructive">{-d}d past deadline</div>}
                    </td>
                    <td className="px-3 py-3.5"><RiskPill risk={o.risk} /></td>
                    <td className="px-3 py-3.5"><StatusPill tone={o.excluded ? "neutral" : STATUS[o.status].tone}>{o.excluded ? "Excluded" : STATUS[o.status].label}</StatusPill></td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-success" style={{ width: `${o.progress}%` }} /></div>
                        <span className="text-xs text-muted-foreground">{o.tasks_done}/{o.task_count}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
      <Sheet open={!!sel} onOpenChange={(o) => !o && setSel(null)}>
        <SheetContent className="w-[560px] overflow-y-auto sm:max-w-[560px]">
          {sel && (
            <>
              <SheetHeader>
                <div className="font-mono text-[11px] text-muted-foreground">{sel.code} · {sel.circular_ref}</div>
                <SheetTitle className="leading-snug">{sel.title}</SheetTitle>
              </SheetHeader>
              <div className="mt-4 space-y-4 px-4 pb-6 text-sm">
                <div className="flex flex-wrap gap-2"><RiskPill risk={sel.risk} /><StatusPill>{sel.category}</StatusPill>{sel.frequency && <StatusPill tone="info">{sel.frequency}</StatusPill>}</div>
                <Citation refLabel={sel.clause_ref} page={sel.page} text={sel.source_text} highlight />
                <Field k="Requirement" v={sel.description} />
                <Field k="Deadline" v={`${sel.deadline ?? "Not stated"}${sel.due_date ? ` (${fmtDate(sel.due_date)})` : ""}`} />
                <Field k="Owner" v={sel.department ? `${sel.department} (${sel.owner})` : "Assigned after Gate 1"} />
                <Field k="Evidence" v={sel.evidence} />
                <Field k="Applicability" v={sel.applicability_reason} />
                {sel.impact && <Field k="Systems" v={sel.impact.systems.join(", ") || "-"} />}
                {sel.ambiguity.length > 0 && (
                  <div>
                    <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Open interpretation questions</div>
                    {sel.ambiguity.map((a, i) => <div key={i} className="mt-1.5 rounded-lg bg-warning/10 p-2.5 text-[13px]"><b>{a.type}:</b> {a.explanation}</div>)}
                  </div>
                )}
                <Field k="Extraction confidence" v={sel.confidence !== null ? `${Math.round((sel.confidence ?? 0) * 100)}%` : "-"} />
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </AppShell>
  );
}

function Field({ k, v }: { k: string; v: string | null | undefined }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className="mt-0.5">{v || "-"}</div>
    </div>
  );
}
