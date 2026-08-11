import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDemo } from "@/lib/demo";
import { formatDateTime } from "@/lib/format";
import { Filter, RefreshCcw, Mail, TriangleAlert, Sparkles, ArrowRight, Play } from "lucide-react";
import { useState } from "react";
import { usePipeline } from "@/hooks/use-pipeline";
import { PipelineProgress } from "@/components/sera/pipeline-progress";
export const Route = createFileRoute("/inbox")({
  head: () => ({ meta: [{ title: "Regulatory Inbox · SERA" }] }),
  component: Inbox,
});

const TABS = ["All Communications", "Flagged", "Analyzing"] as const;

function Inbox() {
  const { circulars, demoStage } = useDemo();
  const navigate = useNavigate();
  const { startPipeline, activeJobId, jobStatus } = usePipeline();
  const [tab, setTab] = useState<(typeof TABS)[number]>("All Communications");
  const filtered = circulars.filter((c) =>
    tab === "Flagged"
      ? c.processingStatus === "Flagged"
      : tab === "Analyzing"
        ? c.processingStatus === "Analyzing"
        : true,
  );

  return (
    <AppShell>
      <PipelineProgress jobStatus={jobStatus} activeJobId={activeJobId} />
      <PageHeader
        title="Regulatory Inbox"
        description="Consolidated feed of global regulatory updates and communications."
        actions={
          <>
            <Button variant="outline" className="gap-2">
              <Filter className="h-4 w-4" /> Filter
            </Button>
            <Button className="gap-2">
              <RefreshCcw className="h-4 w-4" /> Sync Now
            </Button>
          </>
        }
      />

      {/* Stat cards */}
      <section className="grid gap-4 md:grid-cols-3">
        <Card className="rounded-2xl p-5">
          <div className="mb-6 flex items-center justify-between bg-card">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <Mail className="h-4 w-4" />
            </div>
            <StatusPill tone="success">+12%</StatusPill>
          </div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Unread Updates
          </div>
          <div className="mt-1 text-3xl font-semibold tracking-tight">248</div>
        </Card>

        <Card className="rounded-2xl p-5">
          <div className="mb-6 flex items-center justify-between bg-card">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <TriangleAlert className="h-4 w-4" />
            </div>
            <StatusPill tone="danger">CRITICAL</StatusPill>
          </div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            High Risk Flags
          </div>
          <div className="mt-1 text-3xl font-semibold tracking-tight">14</div>
        </Card>

        <Card className="rounded-2xl p-5">
          <div className="flex items-center justify-between bg-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Ingestion Pipeline Status
            </div>
            <div className="text-right text-xs">
              <div className="font-medium text-success">Active</div>
              <div className="text-muted-foreground">Last sync 2m ago</div>
            </div>
          </div>
          <div className="mt-5 flex h-16 items-end gap-1.5">
            {[40, 60, 90, 50, 70, 80, 55, 40, 65, 70, 60, 55].map((h, i) => (
              <div
                key={i}
                className={
                  "flex-1 rounded-sm " +
                  (i === 2 ? "bg-primary" : "bg-primary/25")
                }
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </Card>
      </section>

      {/* Table */}
      <Card className="mt-8 overflow-hidden rounded-2xl p-0 bg-card">
        <div className="flex items-center justify-between border-b border-border px-6 pt-4">
          <div className="flex gap-6">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={
                  "relative pb-3 text-sm font-medium transition " +
                  (t === tab ? "text-foreground" : "text-muted-foreground hover:text-foreground")
                }
              >
                {t}
                {t === tab && (
                  <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-primary" />
                )}
              </button>
            ))}
          </div>
          <div className="pb-3 text-xs text-muted-foreground">
            Showing 1–{filtered.length} of 248 entries
          </div>
        </div>
        <table className="w-full text-sm bg-card">
          <thead>
            <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
              <th className="px-6 py-3">Received</th>
              <th className="px-6 py-3">Source</th>
              <th className="px-6 py-3">Subject</th>
              <th className="px-6 py-3">Processing</th>
              <th className="px-6 py-3">Risk</th>
              <th className="px-6 py-3">Owner</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => {
              const isDemo = c.id === "c-demo";
              return (
                <tr
                  key={c.id}
                  onClick={() => {
                    if (isDemo) {
                      navigate({ to: "/workspace" });
                    }
                  }}
                  className={`border-t border-border transition-colors hover:bg-surface-2/60 ${isDemo ? "bg-amber-500/[0.02] cursor-pointer" : "cursor-pointer"}`}
                >
                  <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">
                    {formatDateTime(c.receivedAt)}
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill tone={isDemo ? "brand" : "neutral"}>{c.source}</StatusPill>
                  </td>
                  <td className="max-w-[420px] px-6 py-4">
                    <div className="flex items-center gap-2 font-medium text-foreground">
                      {c.title}
                      {isDemo && (
                        <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-semibold text-amber-600 dark:text-amber-400">
                          DEMO
                        </span>
                      )}
                    </div>
                    {isDemo ? (
                      <div className="mt-1.5 space-y-1">
                        <div className="text-xs text-muted-foreground font-semibold">
                          Circular No: <span className="font-mono text-foreground font-medium">{c.reference}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Published: <span className="text-foreground font-medium">14 July 2026</span> &middot; Effective: <span className="text-foreground font-medium font-mono">1 Oct 2026</span>
                        </div>
                        <div className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1">
                          Applicability: 
                          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                            Applicable to Stockbrokers
                          </span>
                        </div>
                        <div className="mt-2.5">
                          <Button 
                            size="sm" 
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate({ to: "/workspace" });
                            }}
                            className="h-7 text-xs font-semibold gap-1 bg-primary/15 hover:bg-primary/25 text-primary border-none cursor-pointer px-3 rounded-md"
                          >
                            Review Analysis <ArrowRight className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-0.5 text-xs text-muted-foreground flex items-center gap-2">
                        <span className="truncate max-w-[280px]">{c.summary}</span>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="h-6 text-[10px] px-2 py-0 cursor-pointer border-primary/20 text-primary hover:bg-primary/5"
                          onClick={(e) => {
                            e.stopPropagation();
                            startPipeline(c.id);
                          }}
                        >
                          <Play className="h-3 w-3 mr-1" /> Run Pipeline
                        </Button>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill
                      tone={
                        c.processingStatus === "Analyzing"
                          ? "info"
                          : c.processingStatus === "Flagged"
                            ? "warning"
                            : "success"
                      }
                      dot
                    >
                      {c.processingStatus}
                    </StatusPill>
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill tone={riskTone(c.risk)}>{c.risk}</StatusPill>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">{c.owner ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_360px]">
        <Card className="relative overflow-hidden rounded-2xl border-transparent bg-primary p-6 text-primary-foreground">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="h-4 w-4" /> SERA Intelligence Insight
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-primary-foreground/85">
            Our AI analysis suggests the recent{" "}
            <span className="font-semibold text-primary-foreground underline decoration-primary-foreground/40 underline-offset-2">
              SEBI amendment on Portfolio Managers
            </span>{" "}
            has a 92% correlation with your current institutional reporting workflows. Immediate
            review is recommended to avoid Q4 compliance discrepancies.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <Link
              to="/impact-map"
              className="rounded-md bg-primary-foreground px-4 py-2 text-sm font-medium text-primary hover:opacity-90"
            >
              Go to Impact Map
            </Link>
            <button className="rounded-md border border-primary-foreground/30 px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-foreground/10">
              Acknowledge Alert
            </button>
          </div>
        </Card>

        <Card className="rounded-2xl p-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Recent Activity
          </div>
          <div className="mt-4 space-y-4 text-sm">
            <ActivityLine tone="success" title="Analysis Completed" detail="RBI Master Circular v.2.4" when="12 min ago" />
            <ActivityLine tone="info" title="Draft Generated" detail="Compliance response for SEBI-042" when="2 hours ago" />
            <ActivityLine tone="danger" title="User Flag Added" detail="Marked as critical by S. Gupta" when="4 hours ago" />
          </div>
        </Card>
      </section>
    </AppShell>
  );
}

function ActivityLine({
  tone,
  title,
  detail,
  when,
}: {
  tone: "success" | "info" | "danger";
  title: string;
  detail: string;
  when: string;
}) {
  const color =
    tone === "success" ? "bg-success" : tone === "info" ? "bg-info" : "bg-destructive";
  return (
    <div className="flex gap-3 border-l-2 pl-3" style={{ borderColor: "var(--color-border)" }}>
      <div className={`mt-1.5 h-1.5 w-1.5 rounded-full ${color}`} />
      <div className="min-w-0">
        <div className="font-medium text-foreground">{title}</div>
        <div className="text-xs text-muted-foreground">{detail}</div>
        <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground/70">
          {when}
        </div>
      </div>
    </div>
  );
}
