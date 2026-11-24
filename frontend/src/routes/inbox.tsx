import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useRef, useState } from "react";
import { ArrowRight, CloudDownload, ExternalLink, FileText, Loader2, Play, Search, Upload } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { EmptyState } from "@/components/sera/empty-state";
import { StatusPill } from "@/components/sera/status-pill";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBox, Loading, RiskPill, WfStatusPill } from "@/components/sera/bits";
import { fmtDate, providerLabel, sera, setActiveWorkflow, useCirculars, useSeraMutation, type CircularRow } from "@/lib/sera";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/inbox")({
  head: () => ({ meta: [{ title: "Regulatory Inbox · SERA" }] }),
  validateSearch: (s: Record<string, unknown>): { q?: string } => (typeof s.q === "string" && s.q ? { q: s.q } : {}),
  component: Inbox,
});

const FILTERS = [
  { key: "all", label: "All" },
  { key: "new", label: "Not analysed" },
  { key: "review", label: "Needs approval" },
  { key: "impl", label: "Implementing" },
  { key: "done", label: "Compliant" },
] as const;

function matches(c: CircularRow, f: (typeof FILTERS)[number]["key"]) {
  if (f === "all") return true;
  if (f === "new") return ["created", "failed", "needs_ocr", "changes_requested"].includes(c.status);
  if (f === "review") return c.status === "pending_approval_1" || c.status === "pending_approval_2";
  if (f === "impl") return c.status === "executing";
  return c.status === "compliant";
}

function Inbox() {
  const { q } = Route.useSearch();
  const navigate = useNavigate();
  const { data, error, isLoading } = useCirculars();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all");
  const [query, setQuery] = useState(q ?? "");
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = useSeraMutation((f: File) => sera.upload(f));
  const sync = useSeraMutation(() => sera.sync());
  const analyze = useSeraMutation((id: string) => sera.analyze(id));

  const rows = useMemo(() => {
    const t = query.trim().toLowerCase();
    return (data ?? []).filter((c) => matches(c, filter) && (!t || `${c.title} ${c.reference} ${c.summary ?? ""}`.toLowerCase().includes(t)));
  }, [data, filter, query]);

  const doUpload = (f?: File | null) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) return toast.error("Please choose a PDF circular.");
    toast.promise(upload.mutateAsync(f), {
      loading: `Uploading ${f.name}…`,
      success: (r) => {
        setActiveWorkflow(r.workflow_id);
        return r.created ? "Circular received - analysis started" : "Circular already in SERA - opened it";
      },
      error: (e) => (e as Error).message,
    });
  };

  const open = (c: CircularRow) => {
    if (c.workflow_id) setActiveWorkflow(c.workflow_id);
    navigate({ to: "/workspace" });
  };

  return (
    <AppShell>
      <PageHeader
        eyebrow="Detection & intake"
        title="Regulatory Inbox"
        description="Circulars detected from SEBI or uploaded by your team. Each one becomes a traceable workflow."
        actions={
          <>
            <Button
              variant="outline"
              disabled={sync.isPending}
              onClick={() =>
                toast.promise(sync.mutateAsync(undefined), {
                  loading: "Checking sebi.gov.in for new circulars…",
                  success: (r) => `SEBI sync done: ${r.new} new listing(s), ${r.registered + r.seeded} added to SERA`,
                  error: (e) => (e as Error).message,
                })
              }
            >
              {sync.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <CloudDownload className="mr-1.5 h-4 w-4" />}
              Sync from SEBI
            </Button>
            <Button onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
              <Upload className="mr-1.5 h-4 w-4" /> Upload circular PDF
            </Button>
            <input ref={fileRef} type="file" accept="application/pdf" hidden onChange={(e) => { doUpload(e.target.files?.[0]); e.target.value = ""; }} />
          </>
        }
      />

      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); doUpload(e.dataTransfer.files?.[0]); }}
        className={cn(
          "mb-6 flex items-center justify-center gap-3 rounded-xl border border-dashed px-4 py-5 text-sm text-muted-foreground transition",
          drag ? "border-primary bg-primary/5 text-primary" : "border-border",
        )}
      >
        <FileText className="h-4 w-4" /> Drop any regulator circular PDF here (SEBI, RBI, IRDAI…). It is analysed on this machine.
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-full border border-border bg-surface p-1">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)} className={cn("rounded-full px-3 py-1 text-xs font-medium", filter === f.key ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}>
              {f.label}
              <span className="ml-1 opacity-70">{(data ?? []).filter((c) => matches(c, f.key)).length}</span>
            </button>
          ))}
        </div>
        <div className="relative ml-auto w-72">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter by title or reference" className="h-9 w-full rounded-full border border-border bg-surface pl-8 pr-3 text-sm outline-none focus:border-primary" />
        </div>
      </div>

      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {data && rows.length === 0 && (
        <EmptyState icon={<FileText className="h-5 w-5" />} title="No circulars here" description="Upload a PDF or sync from SEBI to get started." />
      )}
      <div className="space-y-3">
        {rows.map((c) => {
          const canAnalyze = ["created", "failed", "changes_requested", "needs_ocr"].includes(c.status);
          return (
            <Card key={c.id} className="rounded-xl p-5 transition hover:border-primary/30">
              <div className="flex flex-wrap items-start gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                    <StatusPill tone="info">{c.source}</StatusPill>
                    <span className="font-mono">{c.reference}</span>
                    <span>· issued {fmtDate(c.issue_date)}</span>
                    {c.origin === "upload" && <StatusPill>Uploaded</StatusPill>}
                  </div>
                  <button onClick={() => open(c)} className="mt-1.5 text-left text-[15px] font-semibold leading-snug hover:text-primary">{c.title}</button>
                  {c.summary && <p className="mt-1.5 line-clamp-2 text-sm text-muted-foreground">{c.summary}</p>}
                  {c.status === "needs_ocr" && <p className="mt-1.5 text-sm text-destructive">Scanned PDF without a text layer. SERA does not guess, so upload a searchable version.</p>}
                  {c.status === "failed" && <p className="mt-1.5 text-sm text-destructive">{c.error}</p>}
                  {(c.status === "in_analysis" || c.status === "planning") && (
                    <div className="mt-3 h-1 w-64 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${c.progress}%` }} /></div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2">
                    {c.status !== "created" && <RiskPill risk={c.risk} />}
                    <WfStatusPill status={c.status} />
                  </div>
                  {c.obligation_count > 0 && <div className="text-xs text-muted-foreground">{c.obligation_count} obligation(s) · {providerLabel(c.provider)}</div>}
                  <div className="flex gap-2">
                    {c.has_pdf && (
                      <Button size="sm" variant="ghost" asChild>
                        <a href={sera.pdfUrl(c.id)} target="_blank" rel="noreferrer"><ExternalLink className="mr-1 h-3.5 w-3.5" />PDF</a>
                      </Button>
                    )}
                    {canAnalyze ? (
                      <Button size="sm" disabled={!c.has_pdf || analyze.isPending} onClick={() => { if (c.workflow_id) setActiveWorkflow(c.workflow_id); analyze.mutate(c.id, { onSuccess: () => toast.success("Analysis started"), onError: (e) => toast.error(e.message) }); }}>
                        <Play className="mr-1 h-3.5 w-3.5" /> Analyse
                      </Button>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => open(c)}>
                        Open <ArrowRight className="ml-1 h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </AppShell>
  );
}
