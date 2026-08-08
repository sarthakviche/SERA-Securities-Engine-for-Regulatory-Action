import React from "react";
import { Card } from "@/components/ui/card";

export interface ImpactNode {
  col: string;
  code?: string;
  title: string;
  highlight?: boolean;
}

const COLUMNS = [
  { key: "clause", label: "Clause" },
  { key: "obligation", label: "Obligation" },
  { key: "process", label: "Process" },
  { key: "system", label: "Systems" },
  { key: "department", label: "Department" },
  { key: "owner", label: "Owner" },
  { key: "evidence", label: "Evidence" },
];

export function ImpactGraph({ nodes }: { nodes: ImpactNode[] }) {
  return (
    <Card className="overflow-hidden rounded-2xl p-6 bg-card border-border">
      <div
        className="relative rounded-xl border border-dashed border-border bg-surface-2/40 p-6 overflow-x-auto min-w-[800px]"
        style={{
          backgroundImage:
            "radial-gradient(oklch(from var(--color-border) l c h / 60%) 1px, transparent 1px)",
          backgroundSize: "16px 16px",
        }}
      >
        <div className="grid grid-cols-7 gap-4 text-[11px] font-semibold uppercase tracking-[0.1em] text-muted-foreground select-none pb-2 border-b border-border mb-4">
          {COLUMNS.map((c) => (
            <div key={c.key}>{c.label}</div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-4 relative">
          {COLUMNS.map((c) => (
            <div key={c.key} className="flex flex-col gap-3 z-10">
              {nodes
                .filter((n) => n.col === c.key)
                .map((n, i) => (
                  <div
                    key={i}
                    className={
                      "rounded-lg border bg-card p-2.5 text-xs shadow-sm transition " +
                      (n.highlight
                        ? "border-primary ring-2 ring-primary/20"
                        : "border-border hover:border-primary/40 hover:shadow-sm")
                    }
                  >
                    {n.code && (
                      <div className="mb-1 text-[9px] font-bold text-muted-foreground font-mono">
                        {n.code}
                      </div>
                    )}
                    <div className="font-semibold leading-tight text-foreground">{n.title}</div>
                  </div>
                ))}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
