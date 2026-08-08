import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDemo } from "@/lib/demo";
import { formatDate } from "@/lib/format";
import { CheckCircle2, TrendingUp, AlertTriangle, ArrowRight, Play, RefreshCcw } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/implementation-tracker")({
  head: () => ({ meta: [{ title: "Implementation Tracker · SERA" }] }),
  component: Tracker,
});

function Tracker() {
  const {
    demoStage,
    setDemoStage,
    advanceDemo,
    resetDemo,
    obligations,
    tasks,
    isDemoActive,
  } = useDemo();
  const navigate = useNavigate();

  const compliant = obligations.filter((o) => o.status === "Compliant").length;
  const inProgress = obligations.filter((o) => o.status === "In Progress").length;
  const blocked = obligations.filter((o) => o.status === "Blocked" || o.status === "Overdue").length;

  const handleAdvance = () => {
    if (demoStage === "PLAN_APPROVED") {
      setDemoStage("IMPLEMENTING");
      toast.success("Demo Stage Advanced: Development Complete", {
        description: "SOP updated, scheduler configured, database logging code written.",
      });
    } else if (demoStage === "IMPLEMENTING") {
      setDemoStage("EVIDENCE_REVIEW");
      toast.success("Demo Stage Advanced: Evidence Review Mode", {
        description: "QA test report generated. Compliance evidence uploaded and waiting for review.",
      });
    } else if (demoStage === "EVIDENCE_REVIEW") {
      setDemoStage("COMPLIANT");
      toast.success("Demo Stage Advanced: Obligation Compliant", {
        description: "Compliance officer verified evidence. Added to Continuous Monitoring.",
      });
      // Redirect to compliance register
      navigate({ to: "/compliance-register" });
    }
  };

  const handleReset = () => {
    resetDemo();
    toast.success("Demo Reset", {
      description: "Restored system to baseline state.",
    });
    navigate({ to: "/" });
  };

  const getAdvanceButtonText = () => {
    switch (demoStage) {
      case "PLAN_APPROVED":
        return "Advance Stage: SOP & Dev Completed";
      case "IMPLEMENTING":
        return "Advance Stage: QA & Evidence Uploaded";
      case "EVIDENCE_REVIEW":
        return "Verify Evidence & Set Compliant";
      case "COMPLIANT":
        return "Compliant & Monitored";
      default:
        return "Initialize Plan First";
    }
  };

  // Filter tasks to show only demo tasks if active
  const filteredTasks = isDemoActive
    ? tasks.filter((t) => t.obligationId === "o-demo")
    : tasks;

  return (
    <AppShell>
      <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
        <span>Workspace</span>
        <span>/</span>
        <span className="text-foreground">Implementation Tracker</span>
      </div>

      <PageHeader
        title="Implementation Tracker"
        description={
          isDemoActive
            ? "SEBI Circular SEBI/HO/MIRSD/2026/104: Task In-Flight Action Queue & Proof Verification"
            : "Live health of every commitment across the register."
        }
        actions={
          isDemoActive ? (
            <div className="flex gap-2 items-center">
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Progress Control
              </span>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleReset}
                className="gap-1.5 cursor-pointer text-xs h-9"
              >
                <RefreshCcw className="h-3.5 w-3.5" /> Reset
              </Button>
              <Button
                onClick={handleAdvance}
                disabled={demoStage === "COMPLIANT" || demoStage === "OFF" || demoStage === "DETECTED" || demoStage === "ANALYZED" || demoStage === "INTERPRETATION_APPROVED" || demoStage === "IMPACT_MAPPED"}
                className="gap-1.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold shadow border-none cursor-pointer text-xs h-9"
              >
                <Play className="h-3.5 w-3.5 fill-current" /> {getAdvanceButtonText()}
              </Button>
            </div>
          ) : null
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Compliant" value={compliant} icon={<CheckCircle2 className="h-4 w-4" />} tone="success" />
        <MetricCard label="In Progress" value={inProgress} icon={<TrendingUp className="h-4 w-4" />} tone="info" />
        <MetricCard label="At Risk" value={blocked} icon={<AlertTriangle className="h-4 w-4" />} tone="danger" />
      </div>

      <Card className="mt-8 overflow-hidden rounded-2xl p-0 bg-card border-border">
        <div className="border-b border-border px-6 py-4 flex items-center justify-between bg-surface-2/45">
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            {isDemoActive ? "SEBI Client Mobile Re-verification Tasks Breakdown" : "Obligation Progress"}
          </span>
          {isDemoActive && (
            <span className="text-xs text-muted-foreground font-mono">
              Stage Code: <strong className="text-primary">{demoStage}</strong>
            </span>
          )}
        </div>

        {isDemoActive ? (
          // Detailed task tracker layout for Stockbroker re-verification
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-2/30 text-left text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground border-b border-border">
                <th className="px-6 py-3">Task Details</th>
                <th className="px-6 py-3">Assignee</th>
                <th className="px-6 py-3">Due Date</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Progress</th>
                <th className="px-6 py-3">Evidence Item / Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((t) => {
                const evidenceName = getEvidenceName(t.id);
                const isUploaded =
                  (demoStage === "EVIDENCE_REVIEW" || demoStage === "COMPLIANT") &&
                  (t.id !== "t-demo-comp1");
                const isComplianceTask = t.id === "t-demo-comp1";

                return (
                  <tr key={t.id} className="border-t border-border hover:bg-surface-2/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-foreground text-xs leading-normal">{t.title}</div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">Dependency: None</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-foreground/80">{t.assignee}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground font-mono">{formatDate(t.dueDate)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusPill
                        tone={
                          t.status === "Done"
                            ? "success"
                            : t.status === "In Progress"
                              ? "info"
                              : t.status === "Review"
                                ? "warning"
                                : "neutral"
                        }
                        dot
                      >
                        {t.status}
                      </StatusPill>
                    </td>
                    <td className="px-6 py-4 w-40">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-primary transition-all duration-300"
                            style={{ width: `${t.progress}%` }}
                          />
                        </div>
                        <span className="text-[11px] tabular-nums font-mono text-muted-foreground">{t.progress}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-normal">
                      {isComplianceTask ? (
                        demoStage === "EVIDENCE_REVIEW" ? (
                          <Button
                            size="sm"
                            onClick={() => {
                              setDemoStage("COMPLIANT");
                              toast.success("Obligation marked compliant", {
                                description: "Human verification sealed the KYC audit trail.",
                              });
                              navigate({ to: "/compliance-register" });
                            }}
                            className="h-6 text-[10px] bg-primary text-primary-foreground font-semibold cursor-pointer border-none px-2 rounded-md"
                          >
                            Verify & Seal
                          </Button>
                        ) : demoStage === "COMPLIANT" ? (
                          <span className="text-success font-semibold flex items-center gap-1">
                            &bull; Verification Sealed
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Awaiting uploads</span>
                        )
                      ) : isUploaded ? (
                        <div className="flex flex-col">
                          <span className="text-success font-semibold flex items-center gap-1 font-mono text-[10px]">
                            &bull; Uploaded
                          </span>
                          <span className="text-[9.5px] text-muted-foreground underline truncate max-w-[150px]">
                            {evidenceName}
                          </span>
                        </div>
                      ) : t.status === "Done" ? (
                        <span className="text-muted-foreground italic">Generating...</span>
                      ) : (
                        <span className="text-muted-foreground/50">Pending completion</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          // Default baseline mockup rows
          <div className="divide-y divide-border bg-card">
            {obligations.map((o) => (
              <div key={o.id} className="grid grid-cols-[1fr_auto] items-center gap-6 px-6 py-4 hover:bg-surface-2/30 transition-colors">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-muted-foreground">{o.code}</span>
                    <StatusPill tone={riskTone(o.risk)}>{o.risk}</StatusPill>
                  </div>
                  <div className="mt-1 truncate text-sm font-medium">{o.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {o.owner} · {o.department} · due {formatDate(o.dueDate)}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="h-1.5 w-48 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${o.progress}%` }}
                    />
                  </div>
                  <span className="w-10 text-right text-xs tabular-nums text-muted-foreground">
                    {o.progress}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </AppShell>
  );
}

// Map task ID to evidence filename
function getEvidenceName(id: string) {
  switch (id) {
    case "t-demo-it1":
      return "Config_Change_Scheduler.log";
    case "t-demo-it2":
      return "SMS_Gateway_Config.png";
    case "t-demo-it3":
      return "DB_Migration_Logs.sql";
    case "t-demo-ops1":
      return "SOP_Client_Mobile_v2.pdf";
    case "t-demo-cust1":
      return "CRM_Email_Template.html";
    case "t-demo-qa1":
      return "QA_Test_Report_OTP.pdf";
    default:
      return "evidence_file.dat";
  }
}

function MetricCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  tone: "success" | "info" | "danger";
}) {
  return (
    <Card className="rounded-2xl p-5 bg-card border-border">
      <div className="mb-5 flex items-center justify-between">
        <div
          className={
            "flex h-9 w-9 items-center justify-center rounded-lg " +
            (tone === "success"
              ? "bg-success/10 text-success"
              : tone === "info"
                ? "bg-info/10 text-info"
                : "bg-destructive/10 text-destructive")
          }
        >
          {icon}
        </div>
      </div>
      <div className="text-3xl font-semibold tracking-tight text-foreground">{String(value).padStart(2, "0")}</div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </Card>
  );
}
