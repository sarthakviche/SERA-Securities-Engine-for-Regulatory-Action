import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useWorkflow(workflowId: string | null) {
  return useQuery({
    queryKey: ["workflow", workflowId],
    queryFn: () => api.getWorkflowStatus(workflowId!),
    enabled: !!workflowId,
    refetchInterval: (query: any) =>
      // Poll while agents are running, stop once at a gate or terminal state
      ["impact_mapping", "planning"].includes(query.state?.data?.current_stage) ? 3000 : false,
  });
}
