import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

export function usePipeline() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const startPipeline = useMutation({
    mutationFn: async (documentId: string) => {
      const res = await fetch(`/api/v1/pipeline/process/${documentId}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to start pipeline");
      const data = await res.json();
      setActiveJobId(data.job_id);
      return data;
    },
  });

  const jobStatus = useQuery({
    queryKey: ["pipeline", activeJobId],
    queryFn: async () => {
      if (!activeJobId) return null;
      const res = await fetch(`/api/v1/pipeline/jobs/${activeJobId}`);
      if (!res.ok) throw new Error("Failed to fetch job status");
      return res.json();
    },
    enabled: !!activeJobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "COMPLETED" || data?.status === "FAILED") {
        return false;
      }
      return 2000;
    },
  });

  return {
    startPipeline: startPipeline.mutate,
    isStarting: startPipeline.isPending,
    activeJobId,
    jobStatus: jobStatus.data,
  };
}
