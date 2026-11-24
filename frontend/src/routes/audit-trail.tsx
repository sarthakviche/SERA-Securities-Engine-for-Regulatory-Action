import type React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Bot, CheckCircle2, FileSearch, FileUp, Link2, Loader2, ShieldAlert, ShieldCheck, UserCheck } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBox, Loading } from "@/components/sera/bits";
import { sera, useAudit, useCirculars, type AuditRow } from "@/lib/sera";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/audit-trail")({
  head: () => ({ meta: [{ title: "Audit Trail · SERA" }] }),
  component: AuditTrail,
});

const KIND: Record<AuditRow["kind"], { icon: React.ReactElement; tone: "brand" | "info" | "success" | "warning" | "neutral" }> = {
  SYSTEM: { icon: <FileUp className="h-3.5 w-3.5" />, tone: "neutral" },
  AGENT: { icon: <Bot className="h-3.5 w-3.5" />, tone: "info" },
  APPROVAL: { icon: <UserCheck className="h-3.5 w-3.5" />, tone: "success" },
  EVIDENCE: { icon: <CheckCircle2 className="h-3.5 w-3.5" />, tone: "brand" },
  REQUEST: { icon: <FileSearch className="h-3.5 w-3.5" />, tone: "warning" },
};

function AuditTrail() {
  const { data: circulars } = useCirculars();
  const [wf, setWf] = useState<string>("");
  const { data, error, isLoading } = useAudit(wf || undefined);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<{ valid: boolean; checked: number; head?: string; broken_at?: number } | null>(null);

  const verify = async () => {
    setVerifying(true);
    try {
      const r = await sera.verifyAudit();
      setResult(r);
      r.valid ? toast.success(`Chain intact: ${r.checked} events verified`) : toast.error(`Tampering detected at event #${r.broken_at}`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <AppShell>
      <PageHeader
        eyebrow="Tamper-evident"
        title="Audit Trail"
        description="An append-only log of every agent action, human approval and evidence upload. Each event is SHA-256 chained to the previous one, so any edit breaks the chain."
        actions={
          <>
            <select value={wf} onChange={(e) => setWf(e.target.value)} className="h-9 max-w-[280px] rounded-md border border-border bg-surface px-3 text-sm">
              <option value="">All circulars</option>
              {(circulars ?? []).filter((c) => c.workflow_id).map((c) => <option key={c.id} value={c.workflow_id!}>{c.title.slice(0, 60)}</option>)}
            </select>
            <Button onClick={verify} disabled={verifying}>
              {verifying ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-1.5 h-4 w-4" />} Verify chain integrity
            </Button>
          </>
        }
      />
      {result && (
        <Card className={"mb-6 flex items-center gap-3 rounded-2xl p-4 text-sm " + (result.valid ? "border-success/40 bg-success/5" : "border-destructive/40 bg-destructive/5")}>
          {result.valid ? <ShieldCheck className="h-5 w-5 text-success" /> : <ShieldAlert className="h-5 w-5 text-destructive" />}
          <div>
            <div className="font-semibold">{result.valid ? `Integrity verified: all ${result.checked} events are consistent` : `Chain broken at event #${result.broken_at}`}</div>
            {result.head && <div className="font-mono text-[11px] text-muted-foreground">head {result.head}</div>}
          </div>
        </Card>
      )}
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {data && data.length === 0 && <EmptyState title="No events yet" description="Activity is recorded as circulars move through SERA." />}
      <div className="relative space-y-3 pl-6 before:absolute before:bottom-2 before:left-[11px] before:top-2 before:w-px before:bg-border">
        {(data ?? []).map((e) => (
          <div key={e.id} className="relative">
            <span className="absolute -left-6 top-4 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-background text-primary">{KIND[e.kind].icon}</span>
            <Card className="rounded-xl p-4">
              <div className="flex flex-wrap items-center gap-2">
                <StatusPill tone={KIND[e.kind].tone}>{e.kind}</StatusPill>
                <span className="font-medium">{e.title}</span>
                <span className="ml-auto text-xs text-muted-foreground">{formatDateTime(e.at)} · {e.actor}</span>
              </div>
              {e.detail && <div className="mt-1.5 text-[13px] text-muted-foreground">{e.detail}</div>}
              {typeof e.payload?.sha256 === "string" && <div className="mt-1.5 font-mono text-[11px] text-success">file sha256 {e.payload.sha256}</div>}
              <div className="mt-2 flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground"><Link2 className="h-3 w-3" />#{e.id} · {e.hash.slice(0, 16)}… ← {e.prev_hash.slice(0, 10)}…</div>
            </Card>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
