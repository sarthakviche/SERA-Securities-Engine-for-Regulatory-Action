import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldCheck, AlertTriangle, Flag, ArrowRight, Check, X, Edit3 } from "lucide-react";
import { useDemo } from "@/lib/demo";
import { toast } from "sonner";

export const Route = createFileRoute("/workspace")({
  head: () => ({ meta: [{ title: "Regulatory Workspace · SERA" }] }),
  component: Workspace,
});

function Workspace() {
  const { demoStage, setDemoStage, isDemoActive } = useDemo();
  const navigate = useNavigate();

  const handleApproveInterpretation = () => {
    setDemoStage("INTERPRETATION_APPROVED");
    toast.success("AI Interpretation Approved", {
      description: "Obligation OB-MIRSD-104 has been created and marked as Approved.",
    });
    navigate({ to: "/obligations" });
  };

  // Render the Demo Workspace if demo mode is active
  if (isDemoActive) {
    return (
      <AppShell>
        <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
          <Link to="/" className="hover:text-foreground">Workspace</Link>
          <span>/</span>
          <span className="text-foreground">SEBI Circular 2026/104</span>
        </div>

        <PageHeader
          eyebrow="Reviewing Ingestion Analysis"
          title="SEBI Circular SEBI/HO/MIRSD/2026/104"
          description="Periodic Re-verification of Registered Client Mobile Numbers"
          actions={
            <>
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
                Illustrative Demo Scenario
              </span>
              <Button variant="outline">Compare Versions</Button>
              <Button onClick={handleApproveInterpretation} className="gap-2 bg-primary hover:bg-primary/95 text-primary-foreground cursor-pointer">
                <ShieldCheck className="h-4 w-4" /> Approve Interpretation
              </Button>
            </>
          }
        />

        <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
          {/* Document Viewer */}
          <Card className="rounded-2xl p-8 bg-card border-border">
            <div className="mx-auto max-w-2xl">
              <div className="text-center text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-600 dark:text-amber-400 bg-amber-500/10 py-1.5 px-3 rounded-full border border-amber-500/20 max-w-xs mx-auto mb-6">
                Illustrative Demo Scenario
              </div>
              <h2 className="mt-4 text-center font-display text-2xl font-bold uppercase underline decoration-1 underline-offset-4 tracking-tight">
                Securities and Exchange Board of India
              </h2>
              <div className="mt-3 text-center text-xs text-muted-foreground font-mono">
                CIRCULAR NO: SEBI/HO/MIRSD/2026/104 &nbsp; · &nbsp; 14 July 2026
              </div>

              <div className="mt-8 space-y-5 text-[14px] leading-relaxed text-foreground/90 font-sans">
                <div>
                  <div className="font-semibold text-foreground">To,</div>
                  <div className="font-medium text-foreground/80">All Registered Stockbrokers</div>
                  <div className="font-medium text-foreground/80">Association of Stock Brokers of India (ASBI)</div>
                </div>

                <p className="font-bold text-foreground border-l-2 border-primary pl-3 py-1 bg-surface-2/40">
                  Subject: Periodic Re-verification of Registered Client Mobile Numbers
                </p>

                <p>
                  1. In order to strengthen investor protection, mitigate risk of unauthorized
                  trading accounts, and prevent communication slippages, SEBI has reviewed the present client
                  onboarding and contact maintenance guidelines. It has been observed that outdated or inactive client mobile
                  numbers pose operational vulnerabilities in market communications.
                </p>

                <p>
                  2.{" "}
                  <mark className="rounded bg-amber-500/20 dark:bg-amber-500/35 px-1 py-0.5 text-foreground font-medium underline decoration-amber-500/60 decoration-dashed">
                    Stockbrokers shall be mandated to perform a periodic re-verification of the registered
                    mobile numbers of all active clients at least once in every 12 months
                  </mark>
                  . This requirement supersedes the existing circular dated May 18, 2024, which permitted a
                  24-month re-verification interval.
                </p>

                <p>
                  3.{" "}
                  <mark className="rounded bg-amber-500/20 dark:bg-amber-500/35 px-1 py-0.5 text-foreground font-medium underline decoration-amber-500/60 decoration-dashed">
                    The verification must be conducted through an appropriate authenticated mechanism
                  </mark>
                  , and proper audit logs of all verification events, including timestamps and verification outcome,
                  must be retained as compliance evidence for a minimum of 5 years.
                </p>

                <p>
                  4. Registered Stockbrokers are advised to establish necessary technology configurations
                  to comply with this mandate. The provisions of this circular shall come into force with effect from
                  <strong> 1 October 2026</strong>.
                </p>
              </div>
            </div>
          </Card>

          {/* AI Analysis Panel */}
          <aside className="space-y-4">
            <Card className="rounded-2xl p-5 bg-card border-border">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <ShieldCheck className="h-4 w-4 text-primary" /> AI Ingestion Analysis
                </div>
                <StatusPill tone="brand">Extraction Success</StatusPill>
              </div>

              <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Applicability
              </div>
              <Card className="mt-1.5 rounded-xl bg-surface-2 p-3.5 shadow-none border border-border">
                <div className="text-xs font-semibold text-foreground">Stockbrokers (All Segments)</div>
                <p className="mt-1 text-[11px] text-muted-foreground leading-relaxed">
                  Identified 1 primary business segment (Stockbroker Registration) and 3 internal systems impacted. Cadence change requires operational adjustment.
                </p>
              </Card>

              <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Extracted Obligation
              </div>
              <Card className="mt-1.5 rounded-xl p-3.5 shadow-none border border-border bg-background">
                <div className="flex items-center justify-between">
                  <StatusPill tone="brand">OB-MIRSD-104</StatusPill>
                  <span className="text-[10px] text-muted-foreground font-medium">Clause 2, 3</span>
                </div>
                <div className="mt-2 text-xs font-semibold text-foreground">Periodic Client Mobile Re-verification</div>
                <p className="mt-1 text-[11px] text-muted-foreground leading-normal">
                  Mandatory re-verification of registered mobile numbers of all active clients every 12 months with secure audit logging.
                </p>
              </Card>

              <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Delta Analysis (Changes)
              </div>
              <Card className="mt-1.5 rounded-xl border-destructive/20 bg-destructive/5 p-3.5 shadow-none">
                <div className="flex items-center gap-2 text-xs font-semibold text-destructive">
                  <AlertTriangle className="h-3.5 w-3.5" /> Mandate Interval Reduction
                </div>
                <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-lg bg-background border border-border p-2.5 text-xs">
                  <div className="text-center">
                    <div className="text-[9px] uppercase tracking-wide text-muted-foreground">
                      Previous
                    </div>
                    <div className="font-semibold text-muted-foreground line-through">24 Months</div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  <div className="text-center">
                    <div className="text-[9px] uppercase tracking-wide text-muted-foreground">
                      New
                    </div>
                    <div className="font-bold text-foreground">12 Months</div>
                  </div>
                </div>
                <p className="mt-2 text-[10px] text-muted-foreground leading-normal">
                  Decreasing verification cycle will increase SMS delivery load and operational KYC review frequency by 2.0x.
                </p>
              </Card>

              <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Ambiguity Resolved Recommendation
              </div>
              <Card className="mt-1.5 rounded-xl border-warning/30 bg-warning/5 p-3.5 shadow-none">
                <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                  <Flag className="h-3.5 w-3.5 text-warning" /> "Appropriate Authenticated Mechanism"
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground leading-normal">
                  The circular does not specify a mandatory technical method.
                </p>
                <div className="mt-2 rounded bg-background border border-border p-2 text-[10.5px] leading-relaxed">
                  <strong className="text-primary font-semibold">SERA Recommendation:</strong> Use SMS OTP (One-Time Password) verification integrated with existing CRM profiles & SMS gateways.
                  <span className="mt-1 block text-[9.5px] font-medium text-muted-foreground italic">
                    * This is an implementation recommendation, not a regulatory constraint.
                  </span>
                </div>
              </Card>

              <div className="mt-5 pt-3 border-t border-border flex items-center justify-between">
                <div className="text-[11.5px] text-muted-foreground">Analysis Confidence</div>
                <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  98% Confidence
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2">
                <Button variant="outline" size="sm" className="text-xs cursor-pointer">
                  <X className="h-3.5 w-3.5 mr-1" /> Reject
                </Button>
                <Button variant="outline" size="sm" className="text-xs cursor-pointer">
                  <Edit3 className="h-3.5 w-3.5 mr-1" /> Edit
                </Button>
                <Button onClick={handleApproveInterpretation} size="sm" className="text-xs bg-primary hover:bg-primary/95 text-primary-foreground cursor-pointer col-span-1">
                  <Check className="h-3.5 w-3.5 mr-1" /> Approve
                </Button>
              </div>
            </Card>
          </aside>
        </div>
      </AppShell>
    );
  }

  // Fallback to default page (original mockup)
  return (
    <AppShell>
      <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
        <Link to="/" className="hover:text-foreground">Workspace</Link>
        <span>/</span>
        <span className="text-foreground">SEBI Circular 2026/104</span>
      </div>

      <PageHeader
        eyebrow="Reviewing"
        title="SEBI Circular 2026/104"
        description="Cybersecurity Framework for Market Infrastructure Institutions"
        actions={
          <>
            <Button variant="outline">Compare Versions</Button>
            <Button className="gap-2">
              <ShieldCheck className="h-4 w-4" /> Review & Approve
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        {/* Document */}
        <Card className="rounded-2xl p-8 bg-card border-border">
          <div className="mx-auto max-w-2xl">
            <div className="text-center text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Confidential / Regulatory
            </div>
            <h2 className="mt-6 text-center font-display text-3xl underline decoration-2 underline-offset-4">
              CIRCULAR
            </h2>
            <div className="mt-4 text-center text-sm text-muted-foreground font-mono">
              SEBI/HO/MRD/CIR/P/2026/104 &nbsp; · &nbsp; January 15, 2026
            </div>

            <div className="mt-10 space-y-5 text-[15px] leading-relaxed text-foreground/90 font-sans">
              <div>
                <div className="font-medium">To,</div>
                <div>All Stock Exchanges</div>
                <div>All Depositories</div>
                <div>All Clearing Corporations</div>
              </div>
              <p className="font-semibold underline underline-offset-2">
                Subject: Comprehensive Cybersecurity and Cyber Resilience Framework for Market
                Infrastructure Institutions (MIIs)
              </p>
              <p>
                1. It has been observed that the increasing sophistication of cyber threats
                necessitates a more agile and robust response mechanism. In supersession of the
                earlier circular dated March 12, 2023, the following revised framework is being
                implemented with immediate effect.
              </p>
              <p>
                2.{" "}
                <mark className="rounded bg-accent/60 px-1 py-0.5">
                  Section 4.2 (Reporting Timelines): All regulated entities shall now be mandated
                  to submit their Cyber Audit Report on a semi-annual basis.
                </mark>{" "}
                This is a significant shift from the previous annual requirement to ensure
                high-frequency monitoring of technical vulnerabilities.
              </p>
            </div>
          </div>
        </Card>

        {/* AI Analysis panel */}
        <aside className="space-y-4">
          <Card className="rounded-2xl p-5 bg-card border-border">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ShieldCheck className="h-4 w-4 text-primary" /> AI Analysis Engine
              </div>
              <StatusPill tone="brand">Stable v4.2</StatusPill>
            </div>

            <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Applicability
            </div>
            <Card className="mt-2 rounded-xl bg-surface-2 p-4 shadow-none border border-border">
              <div className="text-sm font-semibold">Tier-1 & Tier-2 MIIs</div>
              <p className="mt-1 text-xs text-muted-foreground">
                Identified 12 internal entities requiring alignment. Impact: High Architecture
                Change.
              </p>
            </Card>

            <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Key Obligations
            </div>
            <Card className="mt-2 rounded-xl p-4 shadow-none border border-border bg-background">
              <div className="flex items-center justify-between">
                <StatusPill tone="brand">OB-001</StatusPill>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="mt-2 text-sm font-semibold">Cyber Security Committee Formation</div>
              <p className="mt-1 text-xs text-muted-foreground">
                Mandatory formation of a board-level committee led by a technical Non-Executive
                Director. Deadline: 90 days from circular date.
              </p>
            </Card>

            <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Change Analysis (Delta)
            </div>
            <Card className="mt-2 rounded-xl border-destructive/30 bg-destructive/5 p-4 shadow-none">
              <div className="flex items-center gap-2 text-sm font-semibold text-destructive">
                <AlertTriangle className="h-4 w-4" /> Critical Change: Audit Frequency
              </div>
              <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-lg bg-background border border-border p-3 text-sm">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground font-sans">
                    Previous
                  </div>
                  <div className="font-medium line-through">12 Months</div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground font-sans">
                    Revised
                  </div>
                  <div className="font-semibold text-foreground">6 Months</div>
                </div>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Resource requirement predicted to increase by 2.4x for compliance department.
              </p>
            </Card>

            <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Ambiguity Review
            </div>
            <Card className="mt-2 rounded-xl border-warning/40 bg-warning/10 p-4 shadow-none">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Flag className="h-4 w-4 text-warning" /> Definition Ambiguity: "Emerging
                Infrastructure"
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Circular does not provide specific capitalization or volume thresholds for
                'Emerging' status. Manual clarification with SEBI required.
              </p>
            </Card>
          </Card>

          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">Analysis Confidence</div>
            <div className="text-sm font-semibold text-foreground">94%</div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1">Discard Analysis</Button>
            <Button className="flex-1">Commit to Register</Button>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
