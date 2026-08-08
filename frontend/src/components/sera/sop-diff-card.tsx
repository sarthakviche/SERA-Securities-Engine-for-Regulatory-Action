import React from "react";
import { Card } from "@/components/ui/card";
import { FileText, ArrowRight } from "lucide-react";

export interface SOPDiffCardProps {
  title: string;
  departmentName: string;
  isNewSop: boolean;
  previousContent?: string;
  newContent: string;
}

export function SOPDiffCard({ title, departmentName, isNewSop, previousContent, newContent }: SOPDiffCardProps) {
  return (
    <Card className="rounded-2xl p-5 bg-card border-border mb-4">
      <div className="flex items-center gap-3 border-b border-border pb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
        </div>
        <div>
          <div className="text-sm font-semibold text-foreground">{title}</div>
          <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
            {departmentName}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-[1fr_auto_1fr] gap-4">
        <div className="rounded-xl border border-border bg-surface-2 p-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
            {isNewSop ? "Existing" : "Previous SOP Content"}
          </div>
          {isNewSop ? (
            <div className="text-xs italic text-muted-foreground">No existing SOP found (New Document)</div>
          ) : (
            <div className="text-xs leading-relaxed text-muted-foreground line-through opacity-70">
              {previousContent || "No previous content provided."}
            </div>
          )}
        </div>

        <div className="flex items-center justify-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand/10">
            <ArrowRight className="h-4 w-4 text-brand" />
          </div>
        </div>

        <div className="rounded-xl border border-brand/20 bg-brand/5 p-4 shadow-[0_0_15px_rgba(var(--brand),0.05)]">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-brand">
            Proposed Amendment
          </div>
          <div className="text-xs leading-relaxed text-foreground font-medium">
            {newContent}
          </div>
        </div>
      </div>
    </Card>
  );
}
