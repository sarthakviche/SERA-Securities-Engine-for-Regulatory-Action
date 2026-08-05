import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useDemo } from "@/lib/demo";
import { formatDate } from "@/lib/format";
import { Filter, Plus, FileText, ArrowRight, Clock, User, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { Obligation, ObligationStatus } from "@/lib/types";

export const Route = createFileRoute("/obligations")({
  head: () => ({ meta: [{ title: "Obligations · SERA" }] }),
  component: Obligations,
});

const STATUSES = [
  "All",
  "Approved",
  "Open",
  "In Progress",
  "Blocked",
  "Compliant",
  "Overdue",
] as const;

function Obligations() {
  const { obligations, demoStage, isDemoActive } = useDemo();
  const [status, setStatus] = useState<string>("All");
  const [selectedObligation, setSelectedObligation] = useState<Obligation | null>(null);

  const getDisplayStatus = (o: Obligation) => {
    if (o.id === "o-demo" && demoStage === "INTERPRETATION_APPROVED") {
      return "Approved";
    }
    return o.status;
  };

  const getStatusTone = (s: string) => {
    switch (s) {
      case "Compliant":
      case "Approved":
        return "success" as const;
      case "Blocked":
      case "Overdue":
        return "danger" as const;
      case "In Progress":
        return "info" as const;
      default:
        return "neutral" as const;
    }
  };

  // Filter rows
  const rows = obligations.filter((o) => {
    const displayStat = getDisplayStatus(o);
    if (status === "All") return true;
    return displayStat === status;
  });

  return (
    <AppShell>
      <PageHeader
        title="Obligations Register"
        description="Every mandate translated into an ownable, deadline-bound commitment."
        actions={
          <>
            {isDemoActive && (
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Mode Active
              </span>
            )}
            <Button variant="outline" className="gap-2">
              <Filter className="h-4 w-4" /> Filter
            </Button>
            <Button className="gap-2">
              <Plus className="h-4 w-4" /> New Obligation
            </Button>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={
              "rounded-full border px-3 py-1 text-xs font-medium transition cursor-pointer " +
              (s === status
                ? "border-primary bg-primary text-primary-foreground font-semibold shadow-sm"
                : "border-border bg-surface text-muted-foreground hover:border-primary/40 hover:text-foreground")
            }
          >
            {s}
          </button>
        ))}
      </div>

      <Card className="overflow-hidden rounded-2xl p-0 bg-card border-border">
        <table className="w-full text-sm bg-card">
          <thead>
            <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
              <th className="px-6 py-3">Code</th>
              <th className="px-6 py-3">Obligation</th>
              <th className="px-6 py-3">Owner</th>
              <th className="px-6 py-3">Due</th>
              <th className="px-6 py-3">Risk</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Progress</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => {
              const displayStat = getDisplayStatus(o);
              const isDemo = o.id === "o-demo";
              return (
                <tr
                  key={o.id}
                  onClick={() => setSelectedObligation(o)}
                  className={`cursor-pointer border-t border-border transition-colors hover:bg-surface-2/60 ${isDemo ? "bg-amber-500/[0.02]" : ""}`}
                >
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                    {o.code}
                    {isDemo && (
                      <span className="ml-1.5 block text-[8px] font-bold text-amber-500 uppercase">
                        Demo
                      </span>
                    )}
                  </td>
                  <td className="max-w-[380px] px-6 py-4">
                    <div className="font-medium text-foreground">{o.title}</div>
                    <div className="mt-0.5 truncate text-xs text-muted-foreground font-normal">
                      {o.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-foreground/85">{o.owner}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">
                    {formatDate(o.dueDate)}
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill tone={riskTone(o.risk)}>{o.risk}</StatusPill>
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill tone={getStatusTone(displayStat)} dot>
                      {displayStat}
                    </StatusPill>
                  </td>
                  <td className="w-52 px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${o.progress}%` }}
                        />
                      </div>
                      <span className="text-xs tabular-nums text-muted-foreground">
                        {o.progress}%
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Obligation Details Drawer */}
      <Sheet open={!!selectedObligation} onOpenChange={(open) => !open && setSelectedObligation(null)}>
        <SheetContent className="sm:max-w-[480px] bg-background border-l border-border overflow-y-auto">
          {selectedObligation && (
            <div className="space-y-6">
              <SheetHeader>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-muted-foreground">{selectedObligation.code}</span>
                  <StatusPill tone={getStatusTone(getDisplayStatus(selectedObligation))} dot>
                    {getDisplayStatus(selectedObligation)}
                  </StatusPill>
                </div>
                <SheetTitle className="text-xl font-bold font-display text-foreground mt-2">
                  {selectedObligation.title}
                </SheetTitle>
                <SheetDescription className="text-xs text-muted-foreground">
                  Linked Circular: <strong>{selectedObligation.circularRef}</strong>
                </SheetDescription>
              </SheetHeader>

              {/* Specific Demo Content */}
              {selectedObligation.id === "o-demo" ? (
                <>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground mb-1">
                        Requirement Description
                      </h4>
                      <p className="text-xs text-foreground bg-surface-2 p-3 rounded-lg border border-border leading-relaxed">
                        Verify registered client mobile numbers every 12 months using an authenticated OTP mechanism
                        and retain compliance validation logs for 5 years.
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground mb-1.5">
                        Fictional Source Clauses (SEBI)
                      </h4>
                      <div className="space-y-2 text-xs border-l-2 border-primary/45 pl-3 py-0.5 leading-relaxed italic text-foreground/80">
                        <p>
                          "Stockbrokers shall be mandated to perform a periodic re-verification of the registered
                          mobile numbers of all active clients at least once in every 12 months..."
                        </p>
                        <p>
                          "The verification must be conducted through an appropriate authenticated mechanism, and
                          proper audit logs... must be retained..."
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-surface-2 border border-border p-2.5 rounded-lg text-center">
                        <span className="text-[10px] text-muted-foreground font-semibold uppercase block">Previous Cadence</span>
                        <span className="text-xs font-semibold text-muted-foreground line-through">24 Months</span>
                      </div>
                      <div className="bg-surface-2 border border-border p-2.5 rounded-lg text-center">
                        <span className="text-[10px] text-muted-foreground font-semibold uppercase block">New Mandate</span>
                        <span className="text-xs font-bold text-foreground">12 Months</span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground mb-1">
                        Effective Compliance Date
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-foreground bg-surface-2 p-2 rounded-lg border border-border">
                        <Clock className="h-4 w-4 text-primary" />
                        <span>1 October 2026 &middot; High priority implementation</span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground mb-1.5">
                        Dynamic Version History
                      </h4>
                      <div className="relative space-y-3 pl-4 border-l border-border text-xs">
                        <div className="relative">
                          <span className="absolute -left-[20.5px] top-1 h-2.5 w-2.5 rounded-full bg-success ring-4 ring-background" />
                          <div className="font-semibold text-foreground">v1.0 (14 July 2026)</div>
                          <div className="text-muted-foreground">AI interpretation approved & obligation committed.</div>
                        </div>

                        {demoStage !== "INTERPRETATION_APPROVED" && (
                          <div className="relative">
                            <span className="absolute -left-[20.5px] top-1 h-2.5 w-2.5 rounded-full bg-success ring-4 ring-background" />
                            <div className="font-semibold text-foreground">v1.1 (14 July 2026)</div>
                            <div className="text-muted-foreground">Impact mapping and SOP amendment plan acknowledged.</div>
                          </div>
                        )}

                        {(demoStage === "PLAN_APPROVED" ||
                          demoStage === "IMPLEMENTING" ||
                          demoStage === "EVIDENCE_REVIEW" ||
                          demoStage === "COMPLIANT") && (
                          <div className="relative">
                            <span className="absolute -left-[20.5px] top-1 h-2.5 w-2.5 rounded-full bg-success ring-4 ring-background" />
                            <div className="font-semibold text-foreground">v1.2 (15 July 2026)</div>
                            <div className="text-muted-foreground">Implementation tracker loaded with 7 active tasks.</div>
                          </div>
                        )}

                        {demoStage === "COMPLIANT" && (
                          <div className="relative">
                            <span className="absolute -left-[20.5px] top-1 h-2.5 w-2.5 rounded-full bg-success ring-4 ring-background" />
                            <div className="font-semibold text-foreground">v1.3 (16 July 2026)</div>
                            <div className="text-muted-foreground">Evidence verified by Compliance. Obligation sealed.</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border flex justify-end gap-2">
                    <Button variant="outline" size="sm" onClick={() => setSelectedObligation(null)} className="cursor-pointer">
                      Close
                    </Button>
                    <Link to="/impact-map" className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-3 text-xs font-semibold text-primary-foreground hover:bg-primary/90">
                      View Impact Map <ArrowRight className="ml-1.5 h-3 w-3" />
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  <div className="space-y-4 text-xs text-foreground/80 leading-relaxed">
                    <div>
                      <h4 className="font-semibold uppercase tracking-wider text-muted-foreground">Description</h4>
                      <p className="mt-1 bg-surface-2 p-3 rounded-lg border border-border">{selectedObligation.description}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold uppercase tracking-wider text-muted-foreground">Department</h4>
                        <div className="mt-1 flex items-center gap-1.5"><User className="h-3.5 w-3.5" /> {selectedObligation.department}</div>
                      </div>
                      <div>
                        <h4 className="font-semibold uppercase tracking-wider text-muted-foreground">Risk Level</h4>
                        <div className="mt-1"><StatusPill tone={riskTone(selectedObligation.risk)}>{selectedObligation.risk}</StatusPill></div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-border flex justify-end">
                    <Button variant="outline" size="sm" onClick={() => setSelectedObligation(null)} className="cursor-pointer">
                      Close
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </AppShell>
  );
}
