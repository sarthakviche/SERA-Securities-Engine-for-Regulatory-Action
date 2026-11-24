import { createFileRoute } from "@tanstack/react-router";
import { Download, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBox, Loading, RiskPill, Stat, WfStatusPill } from "@/components/sera/bits";
import { fmtDate, useCirculars, useObligations } from "@/lib/sera";

export const Route = createFileRoute("/compliance-register")({
  head: () => ({ meta: [{ title: "Compliance Register · SERA" }] }),
  component: Register,
});

function csv(rows: (string | number | null | undefined)[][]) {
  return rows.map((r) => r.map((c) => `"${String(c ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
}

function Register() {
  const { data: circulars, error, isLoading } = useCirculars();
  const { data: obs } = useObligations(true);
  const analysed = (circulars ?? []).filter((c) => !["created", "needs_ocr", "failed"].includes(c.status));
  const inScope = (obs ?? []).filter((o) => !o.excluded);
  const compliant = inScope.filter((o) => o.status === "completed").length;

  const exportCsv = () => {
    const rows = [
      ["Obligation code", "Circular", "Clause", "Title", "Category", "Risk", "Deadline", "Due date", "Owner", "Status", "Tasks done", "Source text"],
      ...(obs ?? []).map((o) => [o.code, o.circular_ref, o.clause_ref, o.title, o.category, o.risk, o.deadline, o.due_date, o.department, o.excluded ? "excluded" : o.status, `${o.tasks_done}/${o.task_count}`, o.source_text]),
    ];
    const blob = new Blob([csv(rows)], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `sera-compliance-register-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <AppShell>
      <PageHeader
        eyebrow="Regulator-ready"
        title="Compliance Register"
        description="Status of every analysed circular and obligation, ready for inspection. Export for your board or the regulator."
        actions={<Button variant="outline" onClick={exportCsv} disabled={!obs?.length}><Download className="mr-1.5 h-4 w-4" /> Export CSV</Button>}
      />
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {circulars && analysed.length === 0 && <EmptyState icon={<ShieldCheck className="h-5 w-5" />} title="Nothing to report yet" description="Analysed circulars appear here." />}
      {analysed.length > 0 && (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-4">
            <Stat label="Circulars tracked" value={analysed.length} />
            <Stat label="Fully compliant" value={analysed.filter((c) => c.status === "compliant").length} tone="success" />
            <Stat label="Obligations in scope" value={inScope.length} hint={`${(obs ?? []).length - inScope.length} excluded with rationale`} />
            <Stat label="Obligations met" value={`${compliant}/${inScope.length}`} tone="success" />
          </div>
          <Card className="overflow-hidden rounded-2xl p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                  <th className="px-5 py-3">Circular</th><th className="px-3 py-3">Issued</th><th className="px-3 py-3">Risk</th><th className="px-3 py-3">Obligations met</th><th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {analysed.map((c) => {
                  const mine = inScope.filter((o) => o.workflow_id === c.workflow_id);
                  const met = mine.filter((o) => o.status === "completed").length;
                  return (
                    <tr key={c.id} className="border-t border-border align-top">
                      <td className="max-w-[520px] px-5 py-3.5"><div className="font-mono text-[10px] text-muted-foreground">{c.reference}</div><div className="font-medium leading-snug">{c.title}</div></td>
                      <td className="whitespace-nowrap px-3 py-3.5">{fmtDate(c.issue_date)}</td>
                      <td className="px-3 py-3.5"><RiskPill risk={c.risk} /></td>
                      <td className="px-3 py-3.5">{mine.length ? <StatusPill tone={met === mine.length ? "success" : "warning"}>{met}/{mine.length}</StatusPill> : "-"}</td>
                      <td className="px-5 py-3.5"><WfStatusPill status={c.status} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </AppShell>
  );
}
