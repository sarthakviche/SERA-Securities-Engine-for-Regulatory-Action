import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";

const STAGES = [
  "Regulatory Fetching",
  "Ingestion Pipeline",
  "LLM Extraction",
  "Obligation Agent",
  "Applicability Agent",
  "Ambiguity Agent",
  "Task Generation Agent"
];

export function PipelineProgress({ jobStatus, activeJobId }: { jobStatus: any, activeJobId: string | null }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (jobStatus?.status === "COMPLETED") {
      setTimeout(() => navigate({ to: "/obligations" }), 1000);
    }
  }, [jobStatus, navigate]);

  const isOpen = !!activeJobId && jobStatus?.status !== "COMPLETED";
  const currentStageIndex = STAGES.indexOf(jobStatus?.current_stage || STAGES[0]);

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Processing Regulatory Update</DialogTitle>
          <DialogDescription>
            The SERA AI engine is analyzing the document through {STAGES.length} agentic stages.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {STAGES.map((stage, idx) => {
            const isCompleted = jobStatus?.status === "COMPLETED" || (currentStageIndex > idx && jobStatus?.status !== "FAILED");
            const isCurrent = currentStageIndex === idx && jobStatus?.status === "RUNNING";
            
            return (
              <div key={stage} className="flex items-center gap-3">
                {isCompleted ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : isCurrent ? (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground/30" />
                )}
                <span className={`text-sm font-medium ${isCurrent ? "text-foreground" : isCompleted ? "text-muted-foreground" : "text-muted-foreground/50"}`}>
                  {stage}
                </span>
                {isCurrent && jobStatus?.progress && (
                  <span className="ml-auto text-xs text-muted-foreground">{jobStatus.progress}%</span>
                )}
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
