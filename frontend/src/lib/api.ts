// Empty import or remove the line entirely
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = {
  // Workflow CRUD
  createWorkflow: (documentId: string) =>
    fetch(`${BASE}/api/v1/workflows`, { 
      method: "POST", 
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }) 
    }).then(r => r.json()),

  getWorkflow: (id: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}`).then(r => r.json()),

  getWorkflowStatus: (id: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}/status`).then(r => r.json()),

  submitGate: (id: string, gateName: string, decision: "approved"|"rejected", comment?: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}/gate/${gateName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, comment }),
    }).then(r => r.json()),

  getAgentOutput: (id: string, agentName: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}/agent-output/${agentName}`).then(r => r.json()),

  // Documents
  getDocuments: () =>
    fetch(`${BASE}/api/v1/documents`).then(r => r.json()),

  // Pipeline
  startPipeline: (documentId: string) =>
    fetch(`${BASE}/api/v1/pipeline/process/${documentId}`, { method: "POST" }).then(r => r.json()),

  getPipelineStatus: (jobId: string) =>
    fetch(`${BASE}/api/v1/pipeline/jobs/${jobId}`).then(r => r.json()),

  getPipelineResults: (jobId: string) =>
    fetch(`${BASE}/api/v1/pipeline/results/${jobId}`).then(r => r.json()),
};
