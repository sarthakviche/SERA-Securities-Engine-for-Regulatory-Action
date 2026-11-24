import { Link } from "@tanstack/react-router";
import { AlertTriangle, Check, FileText, Loader2, Quote } from "lucide-react";
import type { ReactNode } from "react";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { EmptyState } from "@/components/sera/empty-state";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { STATUS_LABEL, statusTone, type CircularRow, type Risk, type WfStatus } from "@/lib/sera";

export function RiskPill({ risk }: { risk: Risk | null | undefined }) {
  const r = (risk ?? "LOW") as Risk;
  return (
    <StatusPill tone={riskTone(r)} dot>
      {r}
    </StatusPill>
  );
}

export function WfStatusPill({ status }: { status: WfStatus }) {
  const busy = status === "in_analysis" || status === "planning";
  return (
    <StatusPill tone={statusTone(status)}>
      {busy && <Loader2 className="h-3 w-3 animate-spin" />}
      {STATUS_LABEL[status] ?? status}
    </StatusPill>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-20 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <div className="font-semibold">Something went wrong</div>
        <div className="mt-0.5 text-destructive/80">{error instanceof Error ? error.message : String(error)}</div>
      </div>
    </div>
  );
}

export function NoCircular() {
  return (
    <EmptyState
      icon={<FileText className="h-5 w-5" />}
      title="No circular selected"
      description="Pick a circular from the Regulatory Inbox, or upload a new one, to start the workflow."
      action={
        <Button asChild>
          <Link to="/inbox">Open Regulatory Inbox</Link>
        </Button>
      }
    />
  );
}

export function WorkflowPicker({
  value,
  onChange,
  circulars,
}: {
  value: string | null;
  onChange: (id: string) => void;
  circulars: CircularRow[] | undefined;
}) {
  const options = (circulars ?? []).filter((c) => c.workflow_id);
  return (
    <Select value={value ?? undefined} onValueChange={onChange}>
      <SelectTrigger className="h-9 w-[340px] max-w-full text-left text-xs">
        <SelectValue placeholder="Select a circular…" />
      </SelectTrigger>
      <SelectContent>
        {options.map((c) => (
          <SelectItem key={c.workflow_id!} value={c.workflow_id!} className="text-xs">
            <span className="font-mono text-[10px] text-muted-foreground">{c.reference.slice(0, 22)}</span>{" "}
            {c.title.slice(0, 60)}
            {c.title.length > 60 ? "…" : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

const STEPS: { key: string; label: string; statuses: WfStatus[] }[] = [
  { key: "received", label: "Received", statuses: ["created"] },
  { key: "analysis", label: "AI analysis", statuses: ["in_analysis", "needs_ocr", "failed", "changes_requested"] },
  { key: "gate1", label: "Gate 1 · Interpretation", statuses: ["pending_approval_1"] },
  { key: "plan", label: "Impact & plan", statuses: ["planning"] },
  { key: "gate2", label: "Gate 2 · Plan", statuses: ["pending_approval_2"] },
  { key: "exec", label: "Implementation", statuses: ["executing"] },
  { key: "done", label: "Compliant", statuses: ["compliant"] },
];

export function StageStepper({ status }: { status: WfStatus }) {
  const idx = STEPS.findIndex((s) => s.statuses.includes(status));
  return (
    <ol className="flex flex-wrap items-center gap-1.5">
      {STEPS.map((s, i) => {
        const done = i < idx || status === "compliant";
        const current = i === idx && status !== "compliant";
        return (
          <li key={s.key} className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium",
                done && "border-success/30 bg-success/10 text-success",
                current && "border-primary/40 bg-primary/10 text-primary",
                !done && !current && "border-border text-muted-foreground",
              )}
            >
              {done ? <Check className="h-3 w-3" /> : <span className="font-mono text-[10px]">{i + 1}</span>}
              {s.label}
            </span>
            {i < STEPS.length - 1 && <span className="h-px w-3 bg-border" />}
          </li>
        );
      })}
    </ol>
  );
}

export function Citation({ refLabel, page, text, highlight }: { refLabel: string; page?: number | null; text: string; highlight?: boolean }) {
  return (
    <blockquote
      className={cn(
        "relative rounded-lg border-l-2 bg-surface-2/50 py-2.5 pl-9 pr-3 text-[13px] leading-relaxed text-foreground/85",
        highlight ? "border-primary" : "border-border",
      )}
    >
      <Quote className="absolute left-3 top-3 h-3.5 w-3.5 text-muted-foreground" />
      {text}
      <div className="mt-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {refLabel}
        {page ? ` · page ${page}` : ""} · verbatim source
      </div>
    </blockquote>
  );
}

export function SectionTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{children}</div>
      {right}
    </div>
  );
}

export function Stat({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: ReactNode; tone?: "danger" | "success" | "warning" }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{label}</div>
      <div
        className={cn(
          "mt-1.5 text-2xl font-semibold tracking-tight",
          tone === "danger" && "text-destructive",
          tone === "success" && "text-success",
          tone === "warning" && "text-warning-foreground dark:text-warning",
        )}
      >
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}
