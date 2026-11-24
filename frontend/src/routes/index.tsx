import type React from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  ClipboardList,
  FileSearch,
  MessageSquareWarning,
  ShieldCheck,
  Upload,
  UserCheck,
  FileUp,
  Bot,
} from "lucide-react";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBox, Loading, RiskPill, SectionTitle, WfStatusPill } from "@/components/sera/bits";
import { daysUntil, fmtDate, setActiveWorkflow, useCirculars, useDashboard, useMeta, type AuditRow, type UiStage } from "@/lib/sera";
import { relative } from "@/lib/format";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Dashboard · SERA" }] }),
  component: Dashboard,
});

const STAGES: { key: UiStage; label: string }[] = [
  { key: "RECEIVED", label: "Received" },
  { key: "ANALYSING", label: "Analysing" },
  { key: "AWAITING_APPROVAL", label: "Awaiting Approval" },
  { key: "IMPLEMENTATION", label: "Implementation" },
  { key: "MONITORING", label: "Compliant" },
];

const kindIcon: Record<AuditRow["kind"], React.ReactElement> = {
  SYSTEM: <FileUp className="h-3.5 w-3.5" />,
  AGENT: <Bot className="h-3.5 w-3.5" />,
  APPROVAL: <UserCheck className="h-3.5 w-3.5" />,
  EVIDENCE: <CheckCircle2 className="h-3.5 w-3.5" />,
  REQUEST: <FileSearch className="h-3.5 w-3.5" />,
};

function Dashboard() {
  const { data, error, isLoading } = useDashboard();
  const { data: circulars } = useCirculars();
  const { data: meta } = useMeta();
  const navigate = useNavigate();

  const open = (wf: string | null, to: string) => {
    if (wf) setActiveWorkflow(wf);
    navigate({ to });
  };

  return (
    <AppShell>
      <PageHeader
        display
        eyebrow={meta?.org.name ?? "Regulatory Intelligence"}
        title="Compliance command centre"
        description="Every SEBI circular, from detection to evidence-backed compliance. Agents draft, humans approve, and everything is logged in a tamper-evident audit trail."
        actions={
          <>
            {!meta?.org.onboarded && (
              <Button variant="outline" asChild>
                <Link to="/onboarding">Set up organisation</Link>
              </Button>
            )}
            <Button asChild>
              <Link to="/inbox">
                <Upload className="mr-1.5 h-4 w-4" /> Add circular
              </Link>
            </Button>
          </>
        }
      />
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {data && (
        <>
          <section>
            <SectionTitle>Regulatory pipeline</SectionTitle>
            <Card className="grid grid-cols-2 divide-border rounded-2xl p-0 md:grid-cols-5 md:divide-x">
              {STAGES.map((s) => (
                <Link key={s.key} to="/inbox" className="relative px-6 py-5 transition hover:bg-surface-2/50">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{s.label}</div>
                  <div className={"mt-2 text-3xl font-semibold tracking-tight " + (data.pipeline[s.key] ? "text-foreground" : "text-muted-foreground/50")}>
                    {String(data.pipeline[s.key]).padStart(2, "0")}
                  </div>
                </Link>
              ))}
            </Card>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_360px]">
            <div>
              <SectionTitle right={<Link to="/implementation-tracker" className="text-sm text-primary hover:underline">Open tracker</Link>}>
                Attention required
              </SectionTitle>
              <div className="grid gap-4 md:grid-cols-3">
                <Attention icon={<ClipboardList className="h-4 w-4" />} tone="danger" pill="APPROVE" count={data.attention.urgent_approvals} label="Pending gate approvals" to="/workspace" />
                <Attention icon={<MessageSquareWarning className="h-4 w-4" />} count={data.attention.awaiting_review} label="Need human review (OCR / failed)" to="/inbox" />
                <Attention icon={<AlertTriangle className="h-4 w-4" />} tone="warning" pill="RISK" count={data.attention.implementation_risks} label="Overdue implementation tasks" to="/implementation-tracker" />
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-4">
                {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((r) => (
                  <Card key={r} className="flex items-center justify-between rounded-xl px-4 py-3">
                    <RiskPill risk={r} />
                    <span className="text-xl font-semibold">{data.risk_counts[r]}</span>
                  </Card>
                ))}
              </div>
              <div className="mt-1.5 text-xs text-muted-foreground">Open obligations by risk (deadline proximity, category and penalty clauses).</div>
            </div>

            <Card className="relative overflow-hidden rounded-2xl border-transparent bg-[oklch(0.22_0.06_145)] p-6 text-[oklch(0.95_0.02_90)]">
              <div aria-hidden className="pointer-events-none absolute inset-0 opacity-[0.14]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.4) 1px, transparent 1px)", backgroundSize: "20px 20px" }} />
              <div className="relative">
                <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">Compliance health</div>
                <div className="mt-4 text-5xl font-semibold tracking-tight">{data.health.score === null ? "—" : `${data.health.score}%`}</div>
                <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/15">
                  <div className="h-full rounded-full bg-emerald-400 transition-all" style={{ width: `${data.health.score ?? 0}%` }} />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3 text-xs text-white/75">
                  <div><div className="text-xl font-semibold text-white">{data.health.obligations_completed}/{data.health.obligations_in_scope}</div>obligations met</div>
                  <div><div className="text-xl font-semibold text-white">{data.health.tasks_done}/{data.health.tasks_total}</div>tasks done</div>
                </div>
                {data.health.score === null && <div className="mt-4 text-xs text-white/70">Approve a circular's plan to start tracking.</div>}
              </div>
            </Card>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_360px]">
            <Card className="overflow-hidden rounded-2xl p-0">
              <div className="flex items-center justify-between border-b border-border px-6 py-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Circulars</div>
                <Link to="/inbox" className="text-xs text-primary hover:underline">All {data.circulars_total}</Link>
              </div>
              <table className="w-full text-sm">
                <tbody>
                  {(circulars ?? []).slice(0, 7).map((c) => (
                    <tr key={c.id} className="cursor-pointer border-t border-border first:border-t-0 hover:bg-surface-2/40" onClick={() => open(c.workflow_id, "/workspace")}>
                      <td className="px-6 py-3.5">
                        <div className="line-clamp-1 font-medium">{c.title}</div>
                        <div className="mt-0.5 font-mono text-[10px] text-muted-foreground">{c.reference} · {fmtDate(c.issue_date)}</div>
                      </td>
                      <td className="px-3 py-3.5"><WfStatusPill status={c.status} /></td>
                      <td className="px-3 py-3.5">{c.status !== "created" && <RiskPill risk={c.risk} />}</td>
                      <td className="px-4"><ArrowUpRight className="h-4 w-4 text-muted-foreground" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>

            <div className="space-y-6">
              <Card className="rounded-2xl p-5">
                <SectionTitle>Upcoming deadlines</SectionTitle>
                {data.upcoming.length === 0 && <div className="text-sm text-muted-foreground">No open tasks.</div>}
                <ul className="space-y-3">
                  {data.upcoming.map((t) => {
                    const d = daysUntil(t.due_date);
                    return (
                      <li key={t.id} className="flex items-start justify-between gap-3 text-sm">
                        <div className="min-w-0">
                          <div className="line-clamp-1 font-medium">{t.title}</div>
                          <div className="text-xs text-muted-foreground">{t.department}</div>
                        </div>
                        <StatusPill tone={d !== null && d < 0 ? "danger" : d !== null && d <= 7 ? "warning" : "neutral"}>
                          {d === null ? "—" : d < 0 ? `${-d}d late` : d === 0 ? "today" : `${d}d`}
                        </StatusPill>
                      </li>
                    );
                  })}
                </ul>
              </Card>
              <Card className="rounded-2xl p-5">
                <SectionTitle right={<Link to="/audit-trail" className="text-xs text-primary hover:underline">Audit trail</Link>}>Live activity</SectionTitle>
                <ul className="space-y-3">
                  {data.activity.slice(0, 7).map((a) => (
                    <li key={a.id} className="flex gap-3 text-sm">
                      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">{kindIcon[a.kind]}</span>
                      <div className="min-w-0">
                        <div className="line-clamp-2 leading-snug">{a.title}</div>
                        <div className="text-[11px] text-muted-foreground">{a.actor} · {relative(a.at)}</div>
                      </div>
                    </li>
                  ))}
                  {data.activity.length === 0 && <li className="text-sm text-muted-foreground">No activity yet.</li>}
                </ul>
              </Card>
            </div>
          </section>
          <div className="mt-8 flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5" /> Data stays on this machine (local PostgreSQL). No circular text leaves your network unless you configure an LLM key.
          </div>
        </>
      )}
    </AppShell>
  );
}

function Attention({ icon, count, label, pill, tone, to }: { icon: React.ReactElement; count: number; label: string; pill?: string; tone?: "danger" | "warning"; to: string }) {
  return (
    <Link to={to}>
      <Card className="rounded-2xl p-5 transition hover:border-primary/40">
        <div className="flex items-center justify-between">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">{icon}</span>
          {pill && count > 0 && <StatusPill tone={tone}>{pill}</StatusPill>}
        </div>
        <div className="mt-4 text-3xl font-semibold">{String(count).padStart(2, "0")}</div>
        <div className="mt-1 text-sm text-muted-foreground">{label}</div>
      </Card>
    </Link>
  );
}
