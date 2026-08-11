import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/sera/app-shell";
import { PageHeader } from "@/components/sera/page-header";
import { StatusPill, riskTone } from "@/components/sera/status-pill";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDemo } from "@/lib/demo";
import { formatDate } from "@/lib/format";
import { Download, ShieldCheck, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/compliance-register")({
  head: () => ({ meta: [{ title: "Compliance Register · SERA" }] }),
  component: Register,
});

function Register() {
  const { obligations, demoStage, isDemoActive } = useDemo();

  return (
    <AppShell>
      <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
        <span>Compliance Management</span>
        <span>/</span>
        <span className="text-foreground">Compliance Register</span>
      </div>

      <PageHeader
        title="Compliance Register"
        description="Signed, dated, immutable record of every closed and standing obligation."
        actions={
          <>
            {isDemoActive && (
              <span className="mr-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                Demo Register
              </span>
            )}
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" /> Export
            </Button>
            <Button className="gap-2">
              <ShieldCheck className="h-4 w-4" /> Attest & Seal
            </Button>
          </>
        }
      />

      <Card className="overflow-hidden rounded-2xl p-0 bg-card border-border">
        <table className="w-full text-sm bg-card">
          <thead>
            <tr className="bg-surface-2/60 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
              <th className="px-6 py-3">Code</th>
              <th className="px-6 py-3">Obligation</th>
              <th className="px-6 py-3">Source</th>
              <th className="px-6 py-3">Owner</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Risk</th>
              <th className="px-6 py-3">Attested On / Next Review</th>
            </tr>
          </thead>
          <tbody>
            {obligations.map((o) => {
              const isDemo = o.id === "o-demo";
              const isCompliant = o.status === "Compliant";

              // If it is the demo obligation and we are not compliant yet, we can show it as non-compliant or filter it if desired.
              // Let's show it so that the presenter can see it move into this register!
              return (
                <tr
                  key={o.id}
                  className={`border-t border-border hover:bg-surface-2/60 transition-colors ${isDemo ? "bg-amber-500/[0.02]" : ""}`}
                >
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                    {o.code}
                    {isDemo && (
                      <span className="ml-1.5 block text-[8px] font-bold text-amber-500 uppercase">
                        Demo
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-semibold text-foreground">{o.title}</div>
                    <div className="text-xs text-muted-foreground">{o.department}</div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground font-mono text-xs">{o.circularRef}</td>
                  <td className="px-6 py-4 text-foreground/80">{o.owner}</td>
                  <td className="px-6 py-4">
                    <StatusPill
                      tone={
                        o.status === "Compliant"
                          ? "success"
                          : o.status === "Blocked"
                            ? "danger"
                            : "info"
                      }
                      dot
                    >
                      {o.status}
                    </StatusPill>
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill tone={riskTone(o.risk)}>{o.risk}</StatusPill>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground text-xs leading-normal">
                    {isDemo ? (
                      isCompliant ? (
                        <div className="flex flex-col">
                          <span className="text-success font-semibold flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3 inline" /> 16 Jul 2026
                          </span>
                          <span className="text-[10px] text-muted-foreground italic">
                            Next review: 16 Jul 2027
                          </span>
                        </div>
                      ) : (
                        <span className="italic text-muted-foreground/60">Implementation in-flight</span>
                      )
                    ) : isCompliant ? (
                      formatDate(o.dueDate)
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
