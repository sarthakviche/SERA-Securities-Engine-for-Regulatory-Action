import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, ArrowRight, Building2, Server } from "lucide-react";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBox, Loading, NoCircular, RiskPill, SectionTitle, WorkflowPicker } from "@/components/sera/bits";
import { useActiveWorkflow, useWorkflow } from "@/lib/sera";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/impact-map")({
  head: () => ({ meta: [{ title: "Impact Map · SERA" }] }),
  component: ImpactMap,
});

const ROLE: Record<string, string> = { primary_owner: "Owner", contributor: "Contributor", informed: "Informed" };

function ImpactMap() {
  const [wfId, setWf, circulars] = useActiveWorkflow();
  const { data: wf, error, isLoading } = useWorkflow(wfId);
  const impact = wf?.impact;
  const obs = Object.fromEntries((wf?.obligations ?? []).map((o) => [o.code, o]));

  const deptLoad: Record<string, number> = {};
  const sysLoad: Record<string, number> = {};
  impact?.mappings.forEach((m) => {
    m.departments.forEach((d) => (deptLoad[d.department] = (deptLoad[d.department] ?? 0) + 1));
    m.systems.forEach((s) => (sysLoad[s] = (sysLoad[s] ?? 0) + 1));
  });
  const maxLoad = Math.max(1, ...Object.values(deptLoad));

  return (
    <AppShell>
      <PageHeader
        eyebrow="Organisational impact"
        title="Impact Map"
        description="Which departments, systems and evidence each approved obligation touches. Mappings SERA can't match to your org profile go to human review; it doesn't guess."
        actions={<WorkflowPicker value={wfId} onChange={setWf} circulars={circulars} />}
      />
      {!wfId && circulars && <NoCircular />}
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {wf && !impact && (
        <EmptyState
          icon={<Building2 className="h-5 w-5" />}
          title="No impact map yet"
          description="The impact map is generated once the interpretation is approved at Gate 1."
          action={<Button asChild><Link to="/workspace">Go to Workspace</Link></Button>}
        />
      )}
      {wf && impact && (
        <>
          <div className="mb-6 grid gap-6 lg:grid-cols-[1fr_340px]">
            <Card className="rounded-2xl p-5">
              <SectionTitle>Department load</SectionTitle>
              <div className="space-y-2.5">
                {Object.entries(deptLoad).sort((a, b) => b[1] - a[1]).map(([d, n]) => (
                  <div key={d} className="flex items-center gap-3 text-sm">
                    <div className="w-48 shrink-0 truncate">{d}</div>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${(100 * n) / maxLoad}%` }} />
                    </div>
                    <div className="w-6 text-right font-mono text-xs">{n}</div>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="rounded-2xl p-5">
              <SectionTitle>Systems touched</SectionTitle>
              {Object.keys(sysLoad).length === 0 && <div className="text-sm text-muted-foreground">No system changes identified.</div>}
              <div className="flex flex-wrap gap-2">
                {Object.entries(sysLoad).map(([s, n]) => (
                  <StatusPill key={s} tone="info"><Server className="h-3 w-3" />{s} · {n}</StatusPill>
                ))}
              </div>
              {impact.needs_review.length > 0 && (
                <div className="mt-5 rounded-lg border border-warning/30 bg-warning/10 p-3 text-[13px]">
                  <div className="flex items-center gap-1.5 font-semibold"><AlertTriangle className="h-3.5 w-3.5" /> Needs human mapping</div>
                  {impact.needs_review.map((r, i) => <div key={i} className="mt-1"><span className="font-mono text-[11px]">{r.obligation}</span> - {r.reason}</div>)}
                </div>
              )}
            </Card>
          </div>

          <Card className="overflow-x-auto rounded-2xl p-0">
            <div className="grid min-w-[980px] grid-cols-[150px_1.4fr_1.2fr_1fr_1fr] border-b border-border bg-surface-2/60 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
              <div>Clause</div><div>Obligation</div><div>Departments</div><div>Systems</div><div>Evidence</div>
            </div>
            {impact.mappings.map((m) => {
              const o = obs[m.obligation_code];
              return (
                <div key={m.obligation_code} className="grid min-w-[980px] grid-cols-[150px_1.4fr_1.2fr_1fr_1fr] items-start gap-3 border-b border-border px-5 py-4 text-[13px] last:border-0">
                  <div>
                    <div className="font-mono text-[11px] text-muted-foreground">{o?.clause_ref}</div>
                    <div className="mt-1"><RiskPill risk={o?.risk} /></div>
                  </div>
                  <div>
                    <div className="font-mono text-[10px] text-muted-foreground">{m.obligation_code}</div>
                    <div className="font-medium leading-snug">{m.obligation_title}</div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.departments.map((d) => (
                      <span key={d.department} className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs", d.role === "primary_owner" ? "border-primary/40 bg-primary/10 text-primary" : "border-border", !d.matched && "border-warning/50 bg-warning/10")}>
                        {d.department}<span className="text-[10px] opacity-70">· {ROLE[d.role]}</span>
                      </span>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1.5">{m.systems.length ? m.systems.map((s) => <span key={s} className="rounded-md border border-border px-2 py-0.5 text-xs">{s}</span>) : <span className="text-muted-foreground">-</span>}</div>
                  <div className="text-muted-foreground">{o?.evidence}</div>
                </div>
              );
            })}
          </Card>
          <div className="mt-6 flex justify-end">
            <Button asChild><Link to="/implementation-plan">Review implementation plan <ArrowRight className="ml-1 h-4 w-4" /></Link></Button>
          </div>
        </>
      )}
    </AppShell>
  );
}
