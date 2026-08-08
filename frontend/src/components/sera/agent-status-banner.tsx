import React from "react";
import { Card } from "@/components/ui/card";

export function AgentStatusBanner({
  message,
  subtext,
  icon,
}: {
  message: string;
  subtext?: string;
  icon?: React.ReactNode;
}) {
  return (
    <Card className="rounded-2xl p-4 bg-brand/5 border-brand/20 mb-6 shadow-sm overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-brand/10 to-transparent -translate-x-[100%] animate-[shimmer_2s_infinite]" />
      <div className="flex items-center gap-4 relative z-10">
        {icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand/10 text-brand">
            {icon}
          </div>
        )}
        <div>
          <div className="font-semibold text-foreground text-sm">{message}</div>
          {subtext && <div className="text-xs text-muted-foreground mt-0.5">{subtext}</div>}
        </div>
      </div>
    </Card>
  );
}
