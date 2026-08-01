import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useDemo } from "@/lib/demo";
import { formatDateTime } from "@/lib/format";
import {
  CheckCircle2,
  FileText,
  AlertCircle,
  ShieldCheck,
  FileCheck2,
  ExternalLink,
  FolderInput,
  Eye,
  Lock,
} from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/audit-trail")({
  head: () => ({ meta: [{ title: "Audit Trail · SERA" }] }),
  component: Audit,
});

interface AttachmentDetails {
  name: string;
  size: string;
  type: string;
  author: string;
  signed: string;
  snippet: string;
}

const ATTACHMENT_META: Record<string, AttachmentDetails> = {
  "SOP_Client_Mobile_v2.pdf": {
    name: "SOP_Client_Mobile_v2.pdf",
    size: "1.4 MB",
    type: "PDF Document (Acrobat PDF/A)",
    author: "Sarah Miller (Operations Owner)",
    signed: "e-Signed & Sealed (SHA-256: 8f3c...da21)",
    snippet: "Section 4.2: Registered client contact credentials must be re-verified at least once every 12 months using the SMS OTP gateway. All failure attempts must trigger customer operations support tickets.",
  },
  "Config_Change_Scheduler.log": {
    name: "Config_Change_Scheduler.log",
    size: "256 KB",
    type: "ASCII Plain Text Log",
    author: "IT Deployment Pipelines (Jenkins Admin)",
    signed: "System Verified (Checksum: e991...aa40)",
    snippet: "[2026-07-15 14:10:22] WARN: Deprecated parameter client.reverify.interval.days = 730\n[2026-07-15 14:10:23] INFO: Applied new config client.reverify.interval.days = 365\n[2026-07-15 14:10:23] INFO: Configuration reload complete. CRM scheduler restarted successfully.",
  },
  "QA_Test_Report_OTP.pdf": {
    name: "QA_Test_Report_OTP.pdf",
    size: "2.1 MB",
    type: "PDF Document (TestCafe Report)",
    author: "Rohan Kapoor (QA Lead)",
    signed: "Approved (Sign-off: rh.kp@sera.internal)",
    snippet: "Execution Summary: 140 Test Cases run, 140 Passed, 0 Failed.\nValidated Mobile OTP entry screens, database verification logging database hooks, and retry locking mechanisms after 3 unsuccessful attempts.",
  },
};

function Audit() {
  const { auditEvents, isDemoActive } = useDemo();
  const [selectedAttachment, setSelectedAttachment] = useState<AttachmentDetails | null>(null);

  const handleOpenAttachment = (name: string) => {
    const meta = ATTACHMENT_META[name];
    if (meta) {
      setSelectedAttachment(meta);
    } else {
      setSelectedAttachment({
        name,
        size: "Unknown Size",
        type: "System Artifact",
        author: "SERA System Engine",
        signed: "Verified & Locked",
        snippet: "This compliance proof artifact has been securely archived and sealed in SERA evidence vault.",
      });
    }
  };

  return (
    <AppShell>
      <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
        <span>Compliance Management</span>
        <span>/</span>
        <span className="text-foreground">Verification Layer</span>
      </div>

      <PageHeader
        title="Audit Trail & Proof"
        description={
          isDemoActive
            ? "SEBI Circular SEBI/HO/MIRSD/2026/104: Dynamic Cryptographic Compliance Ledger"
            : "Immutable record of evidence review and approval cycles."
        }
        actions={
          <>
            {isDemoActive && (
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Audit Log
              </span>
            )}
            <Button variant="outline" className="gap-2">
              <FolderInput className="h-4 w-4" /> Request More Evidence
            </Button>
            <Button className="gap-2">
              <ShieldCheck className="h-4 w-4" /> Verify Selected Items
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Verification History list */}
        <Card className="rounded-2xl p-6 bg-card border-border">
          <div className="mb-4 flex items-center justify-between border-b border-border pb-3">
            <div className="text-sm font-semibold text-foreground">Verification History</div>
            <select className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground outline-none">
              <option>All Events</option>
              <option>Approvals</option>
              <option>Evidence</option>
              <option>Requests</option>
            </select>
          </div>

          <ol className="relative space-y-6 border-l border-border pl-6">
            {auditEvents.map((e) => (
              <li key={e.id} className="relative">
                <span
                  className={
                    "absolute -left-[30px] top-0 flex h-6 w-6 items-center justify-center rounded-full " +
                    (e.kind === "APPROVAL"
                      ? "bg-primary text-primary-foreground"
                      : e.kind === "EVIDENCE"
                        ? "bg-muted text-muted-foreground"
                        : "bg-destructive/10 text-destructive")
                  }
                >
                  {e.kind === "APPROVAL" && <CheckCircle2 className="h-3.5 w-3.5" />}
                  {e.kind === "EVIDENCE" && <FileText className="h-3.5 w-3.5" />}
                  {e.kind === "REQUEST" && <AlertCircle className="h-3.5 w-3.5" />}
                  {e.kind === "SYSTEM" && <Lock className="h-3.5 w-3.5" />}
                </span>

                <Card className="rounded-xl p-4 shadow-none border border-border bg-background/50 hover:bg-background/80 transition-colors">
                  <div className="flex items-center justify-between">
                    <StatusPill
                      tone={
                        e.kind === "APPROVAL"
                          ? "success"
                          : e.kind === "REQUEST"
                            ? "danger"
                            : e.kind === "SYSTEM"
                              ? "brand"
                              : "neutral"
                      }
                    >
                      {e.kind === "APPROVAL"
                        ? "Final Verification"
                        : e.kind === "EVIDENCE"
                          ? "Evidence Review"
                          : e.kind === "SYSTEM"
                            ? "System Audit log"
                            : "Action Required"}
                    </StatusPill>
                    <div className="text-right text-xs text-muted-foreground">
                      {formatDateTime(e.at)}
                      {e.hash && <div className="text-[9px] tracking-wider font-mono text-primary/70">SEAL: {e.hash}</div>}
                    </div>
                  </div>
                  <div className="mt-2 text-xs font-bold text-foreground">{e.title}</div>
                  <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{e.detail}</p>

                  {e.kind === "APPROVAL" && (
                    <div className="mt-3 flex items-center justify-between rounded-lg border border-border bg-surface-2/60 px-3 py-2 text-xs">
                      <span className="text-muted-foreground text-[10.5px]">Verified by: <strong>{e.actor}</strong></span>
                      <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                  )}

                  {e.attachments && (
                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      {e.attachments.map((a) => (
                        <div
                          key={a.name}
                          onClick={() => handleOpenAttachment(a.name)}
                          className="flex items-center gap-2 rounded-lg border border-border bg-surface-2 hover:border-primary/40 hover:bg-surface-2/90 cursor-pointer p-2 text-xs transition"
                        >
                          <FileCheck2 className="h-4 w-4 text-success shrink-0" />
                          <div className="min-w-0 flex-1">
                            <div className="truncate font-semibold text-foreground text-[11px]">{a.name}</div>
                            <div className="text-[9px] uppercase tracking-wide text-muted-foreground">
                              {a.size} &middot; Click to inspect
                            </div>
                          </div>
                          <Eye className="h-3 w-3 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100" />
                        </div>
                      ))}
                    </div>
                  )}

                  {e.kind === "REQUEST" && (
                    <div className="mt-3 text-xs">
                      <span className="text-muted-foreground">Directed to: </span>
                      <StatusPill tone="neutral">{e.actor}</StatusPill>
                    </div>
                  )}
                </Card>
              </li>
            ))}
          </ol>
        </Card>

        {/* Sidebar Info Panel */}
        <aside className="space-y-4">
          <Card className="rounded-2xl border-transparent bg-[oklch(0.22_0.06_145)] p-5 text-[oklch(0.95_0.02_90)]">
            <div className="text-sm font-semibold">Cryptographic Vault</div>
            <p className="mt-2 text-xs text-white/70 leading-relaxed">
              Every stage approval, task confirmation, and evidence seal publishes a cryptographic proof hash on the internal compliance ledger.
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="uppercase tracking-wider text-white/80 font-bold font-mono">SEAL BLOCK ACTIVE</span>
            </div>
          </Card>

          <Card className="rounded-2xl p-5 bg-card border-border">
            <div className="text-sm font-semibold text-foreground border-b border-border pb-2.5 mb-2.5">Version Control</div>
            <div className="mt-3 space-y-3 text-sm">
              <VersionRow v="v2.0" title="12M KYC Cadence Update" sub="Attestation sealed by D. Narlawar" />
              <VersionRow v="v1.1" title="Proposed SMS OTP Plan" sub="IT scheduler config change locked" />
              <VersionRow v="v1.0" title="Initial Mandate Ingestion" sub="Analyzed & applicability check passed" />
            </div>
          </Card>

          <Card className="rounded-2xl bg-surface-2 p-5 shadow-none border border-border">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Audit Metrics
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-foreground">
                <span>Evidence Verified</span>
                <span className="font-semibold">100%</span>
              </div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-primary" style={{ width: "100%" }} />
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between text-xs text-foreground">
              <span>Avg. Review Time</span>
              <span className="font-semibold">4.8 Hours</span>
            </div>
          </Card>
        </aside>
      </div>

      {/* Evidence Viewer Dialog */}
      <Dialog open={!!selectedAttachment} onOpenChange={(open) => !open && setSelectedAttachment(null)}>
        <DialogContent className="sm:max-w-[480px] bg-background border-border">
          {selectedAttachment && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-1.5 text-success font-semibold text-xs tracking-wider uppercase mb-1">
                  <ShieldCheck className="h-4 w-4" /> Compliance Proof Artifact
                </div>
                <DialogTitle className="text-lg font-bold font-display text-foreground">
                  {selectedAttachment.name}
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground">
                  File Size: <strong>{selectedAttachment.size}</strong> &middot; Format: <strong>{selectedAttachment.type}</strong>
                </DialogDescription>
              </DialogHeader>

              <div className="my-4 space-y-3.5 text-xs">
                <div>
                  <span className="font-semibold text-muted-foreground block uppercase text-[10px] tracking-wider">Author / Publisher</span>
                  <span className="text-foreground font-medium text-xs">{selectedAttachment.author}</span>
                </div>

                <div>
                  <span className="font-semibold text-muted-foreground block uppercase text-[10px] tracking-wider">Ledger Security seal</span>
                  <span className="text-primary font-bold font-mono text-[11px]">{selectedAttachment.signed}</span>
                </div>

                <div>
                  <span className="font-semibold text-muted-foreground block uppercase text-[10px] tracking-wider mb-1.5">Evidence Snippet / Code Extract</span>
                  <pre className="p-3 bg-surface border border-border text-foreground font-mono rounded-lg overflow-x-auto text-[10.5px] leading-relaxed whitespace-pre-wrap">
                    {selectedAttachment.snippet}
                  </pre>
                </div>
              </div>

              <DialogFooter className="border-t border-border pt-3 mt-4">
                <Button onClick={() => setSelectedAttachment(null)} className="bg-primary text-primary-foreground cursor-pointer">
                  Close Document
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}

function VersionRow({ v, title, sub }: { v: string; title: string; sub: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-10 shrink-0 rounded-md bg-muted px-1.5 py-0.5 text-center text-[9px] font-semibold tracking-wide text-muted-foreground uppercase font-mono">
        {v}
      </div>
      <div>
        <div className="text-xs font-semibold text-foreground">{title}</div>
        <div className="text-[10px] text-muted-foreground">{sub}</div>
      </div>
    </div>
  );
}
