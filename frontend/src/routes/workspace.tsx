import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, Check, CircleHelp, ExternalLink, Loader2, Play, ShieldCheck, X } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Citation, ErrorBox, Loading, NoCircular, RiskPill, SectionTitle, StageStepper, Stat, WfStatusPill, WorkflowPicker } from "@/components/sera/bits";
import { fmtDate, providerLabel, sera, useActiveWorkflow, useSeraMutation, useWorkflow, type ObligationRow } from "@/lib/sera";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace")({
  head: () => ({ meta: [{ title: "Regulatory Workspace · SERA" }] }),
  component: Workspace,
});

function Workspace() {
  const [wfId, setWf, circulars] = useActiveWorkflow();
  const { data: wf, error, isLoading } = useWorkflow(wfId);
  const [included, setIncluded] = useState<Record<string, boolean>>({});
  const [focus, setFocus] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [rejecting, setRejecting] = useState(false);

  useEffect(() => {
    if (wf) setIncluded(Object.fromEntries(wf.obligations.map((o) => [o.code, !o.excluded])));
  }, [wf?.circular.id, wf?.obligations.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const gate = useSeraMutation((a: { decision: "approved" | "rejected" }) =>
    sera.gate(wfId!, "gate_1", a.decision, comment || undefined, Object.entries(included).filter(([, v]) => !v).map(([k]) => k)),
  );
  const analyze = useSeraMutation((id: string) => sera.analyze(id));

  const citedRefs = useMemo(() => new Set((wf?.obligations ?? []).map((o) => o.clause_ref)), [wf]);
  const focusRef = wf?.obligations.find((o) => o.code === focus)?.clause_ref;
  const pending = wf?.status === "pending_approval_1";
  const inScope = Object.values(included).filter(Boolean).length;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Interpretation · Gate 1"
        title="Regulatory Workspace"
        description="Review what SERA extracted. Every obligation quotes its source clause verbatim. Approve the interpretation to start impact mapping."
        actions={<WorkflowPicker value={wfId} onChange={setWf} circulars={circulars} />}
      />
      {!wfId && circulars && <NoCircular />}
      {error && <ErrorBox error={error} />}
      {isLoading && <Loading />}
      {wf && (
        <>
          <Card className="mb-6 rounded-2xl p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-mono">{wf.analysis?.circular_number ?? wf.circular.reference}</span>
                  <span>· {fmtDate(wf.analysis?.circular_date ?? wf.circular.issue_date)}</span>
                  {wf.analysis?.addressees?.length ? <span>· To: {wf.analysis.addressees.join(", ")}</span> : null}
                </div>
                <h2 className="mt-2 font-display text-2xl leading-tight">{wf.circular.title}</h2>
                {wf.analysis?.summary && <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{wf.analysis.summary}</p>}
              </div>
              <div className="flex flex-col items-end gap-2">
                <WfStatusPill status={wf.status} />
                {wf.circular.has_pdf && (
                  <a className="inline-flex items-center gap-1 text-xs text-primary hover:underline" href={sera.pdfUrl(wf.circular.id)} target="_blank" rel="noreferrer">
                    Original PDF <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
            <div className="mt-5"><StageStepper status={wf.status} /></div>
          </Card>

          {(wf.status === "created" || wf.status === "failed" || wf.status === "changes_requested") && (
            <Card className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
              <div className="text-sm">
                {wf.status === "changes_requested" ? (
                  <>Interpretation was rejected: <em>{wf.approvals.gate_1?.comment}</em>. Re-run the analysis after reviewing.</>
                ) : wf.status === "failed" ? (
                  <span className="text-destructive">Analysis failed: {wf.circular.error}</span>
                ) : (
                  "This circular has not been analysed yet."
                )}
              </div>
              <Button onClick={() => analyze.mutate(wf.circular.id, { onError: (e) => toast.error(e.message) })} disabled={analyze.isPending || !wf.circular.has_pdf}>
                <Play className="mr-1.5 h-4 w-4" /> Run analysis
              </Button>
            </Card>
          )}
          {wf.status === "in_analysis" && (
            <Card className="mb-6 rounded-2xl p-8 text-center">
              <Loader2 className="mx-auto h-6 w-6 animate-spin text-primary" />
              <div className="mt-3 font-medium">Analysing circular… ({wf.current_stage.replaceAll("_", " ")})</div>
              <div className="mx-auto mt-3 h-1.5 w-80 overflow-hidden rounded-full bg-muted"><div className="h-full bg-primary transition-all" style={{ width: `${wf.progress}%` }} /></div>
            </Card>
          )}
          {wf.status === "needs_ocr" && (
            <Card className="mb-6 flex items-start gap-3 rounded-2xl border-destructive/30 p-6 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-destructive" />
              <div>
                <div className="font-semibold">Fail-closed: no machine-readable text</div>
                <div className="mt-1 text-muted-foreground">{wf.analysis?.summary} Upload a searchable PDF from the Inbox.</div>
              </div>
            </Card>
          )}

          {wf.analysis && wf.obligations.length > 0 && (
            <>
              <div className="mb-6 grid gap-4 md:grid-cols-4">
                <Stat label="Requirements found" value={wf.analysis.obligations} hint={`${wf.analysis.paragraphs.length} paragraphs read`} />
                <Stat label="Applicable to you" value={wf.analysis.applicable} hint="based on your entity profile" />
                <Stat label="Need interpretation" value={wf.obligations.filter((o) => o.ambiguity.length).length} hint={`${wf.analysis.ambiguities} ambiguity flag(s)`} tone={wf.analysis.ambiguities ? "warning" : undefined} />
                <Stat label="Engine" value={<span className="text-base">{providerLabel(wf.analysis.provider)}</span>} hint="citations verified against source" />
              </div>

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)]">
                <Card className="max-h-[calc(100vh-180px)] overflow-y-auto rounded-2xl p-5 lg:sticky lg:top-20">
                  <SectionTitle>Source text</SectionTitle>
                  <div className="space-y-2">
                    {wf.analysis.paragraphs.map((p) => (
                      <div
                        key={p.ref + p.text.slice(0, 20)}
                        className={cn(
                          "rounded-lg px-3 py-2 text-[13px] leading-relaxed transition",
                          citedRefs.has(p.ref) && "bg-primary/5",
                          focusRef === p.ref && "bg-primary/15 ring-1 ring-primary/40",
                        )}
                      >
                        <span className="mr-2 font-mono text-[10px] text-muted-foreground">{p.ref}</span>
                        {p.text}
                      </div>
                    ))}
                  </div>
                </Card>

                <div className="space-y-4">
                  <SectionTitle right={<span className="text-xs text-muted-foreground">{inScope} of {wf.obligations.length} in scope</span>}>
                    Extracted obligations
                  </SectionTitle>
                  {wf.obligations.map((o) => (
                    <ObligationCard
                      key={o.id}
                      o={o}
                      editable={pending}
                      included={included[o.code] ?? !o.excluded}
                      onToggle={(v) => setIncluded((s) => ({ ...s, [o.code]: v }))}
                      focused={focus === o.code}
                      onFocus={() => setFocus(o.code)}
                    />
                  ))}
                </div>
              </div>

              {pending ? (
                <Card className="sticky bottom-4 z-20 mt-6 rounded-2xl border-primary/30 p-5 shadow-xl">
                  <div className="flex flex-wrap items-center gap-4">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                    <div className="min-w-0 flex-1 text-sm">
                      <div className="font-semibold">Gate 1: approve this interpretation?</div>
                      <div className="text-muted-foreground">{inScope} obligation(s) will move to impact mapping. Excluded items are kept as waived, with your decision on record.</div>
                    </div>
                    {rejecting ? (
                      <div className="flex w-full items-end gap-2 md:w-auto">
                        <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="What should be re-interpreted?" className="min-h-[40px] md:w-80" />
                        <Button variant="destructive" disabled={!comment.trim() || gate.isPending} onClick={() => gate.mutate({ decision: "rejected" }, { onSuccess: () => { toast("Interpretation sent back"); setRejecting(false); }, onError: (e) => toast.error(e.message) })}>Send back</Button>
                        <Button variant="ghost" onClick={() => setRejecting(false)}>Cancel</Button>
                      </div>
                    ) : (
                      <>
                        <Button variant="outline" onClick={() => setRejecting(true)}><X className="mr-1.5 h-4 w-4" /> Reject</Button>
                        <Button disabled={gate.isPending || inScope === 0} onClick={() => gate.mutate({ decision: "approved" }, { onSuccess: () => toast.success("Interpretation approved. Impact map and plan are drafted."), onError: (e) => toast.error(e.message) })}>
                          {gate.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Check className="mr-1.5 h-4 w-4" />} Approve interpretation
                        </Button>
                      </>
                    )}
                  </div>
                </Card>
              ) : (
                wf.approvals.gate_1 && (
                  <Card className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl p-5 text-sm">
                    <div>
                      <StatusPill tone={wf.approvals.gate_1.decision === "approved" ? "success" : "danger"}>Gate 1 {wf.approvals.gate_1.decision}</StatusPill>
                      <span className="ml-2 text-muted-foreground">by {wf.approvals.gate_1.by} · {fmtDate(wf.approvals.gate_1.at)}{wf.approvals.gate_1.comment ? ` · "${wf.approvals.gate_1.comment}"` : ""}</span>
                    </div>
                    {wf.approvals.gate_1.decision === "approved" && (
                      <Button asChild size="sm"><Link to="/implementation-plan">Implementation plan <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link></Button>
                    )}
                  </Card>
                )
              )}
            </>
          )}
          {wf.analysis && wf.obligations.length === 0 && wf.status !== "in_analysis" && wf.status !== "needs_ocr" && (
            <Card className="rounded-2xl p-6 text-sm text-muted-foreground">No actionable requirements were found in this circular (informational only).</Card>
          )}
        </>
      )}
    </AppShell>
  );
}

function ObligationCard({ o, editable, included, onToggle, focused, onFocus }: { o: ObligationRow; editable: boolean; included: boolean; onToggle: (v: boolean) => void; focused: boolean; onFocus: () => void }) {
  return (
    <Card onMouseEnter={onFocus} className={cn("rounded-xl p-5 transition", focused && "border-primary/40", !included && "opacity-60")}>
      <div className="flex items-start gap-3">
        {editable && <Checkbox checked={included} onCheckedChange={(v) => onToggle(!!v)} className="mt-1" aria-label="Include in scope" />}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] text-muted-foreground">{o.code}</span>
            <RiskPill risk={o.risk} />
            <StatusPill>{o.category}</StatusPill>
            {!o.applicable && <StatusPill tone="neutral">Not applicable</StatusPill>}
            {o.confidence !== null && <span className="ml-auto text-[11px] text-muted-foreground">confidence {Math.round((o.confidence ?? 0) * 100)}%</span>}
          </div>
          <div className="mt-2 font-semibold leading-snug">{o.title}</div>
          <div className="mt-3"><Citation refLabel={o.clause_ref} page={o.page} text={o.source_text} highlight={focused} /></div>
          <div className="mt-3 grid gap-2 text-[13px] md:grid-cols-2">
            <div><span className="text-muted-foreground">Deadline: </span>{o.deadline ?? "Not stated"}{o.due_date ? ` (${fmtDate(o.due_date)})` : ""}</div>
            <div><span className="text-muted-foreground">Evidence: </span>{o.evidence}</div>
          </div>
          <div className="mt-2 text-[13px]"><span className="text-muted-foreground">Applicability: </span>{o.applicability_reason}</div>
          {o.ambiguity.length > 0 && (
            <div className="mt-3 space-y-1.5 rounded-lg border border-warning/30 bg-warning/10 p-3">
              {o.ambiguity.map((a, i) => (
                <div key={i} className="flex gap-2 text-[12.5px]">
                  <CircleHelp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning-foreground dark:text-warning" />
                  <div><span className="font-semibold">{a.type}</span> - "{a.term}": {a.explanation}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
