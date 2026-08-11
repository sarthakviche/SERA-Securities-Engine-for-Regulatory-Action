// Empty import or remove the line entirely
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = {
  // Workflow CRUD
  createWorkflow: (documentId: string) =>
    fetch(`${BASE}/api/v1/workflows`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }),
    }).then((r) => r.json()),

  getWorkflow: (id: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}`).then((r) => r.json()),

  getWorkflowStatus: (id: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}/status`).then((r) => r.json()),

  submitGate: (
    id: string,
    gateName: string,
    decision: "approved" | "rejected",
    comment?: string,
  ) =>
    fetch(`${BASE}/api/v1/workflows/${id}/gate/${gateName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, comment }),
    }).then((r) => r.json()),

  getAgentOutput: (id: string, agentName: string) =>
    fetch(`${BASE}/api/v1/workflows/${id}/agent-output/${agentName}`).then(
      (r) => r.json(),
    ),

  // Documents
  getDocuments: () =>
    fetch(`${BASE}/api/v1/documents`).then((r) => r.json()),

  // Pipeline
  startPipeline: (documentId: string) =>
    fetch(`${BASE}/api/v1/pipeline/process/${documentId}`, {
      method: "POST",
    }).then((r) => r.json()),

  getPipelineStatus: (jobId: string) =>
    fetch(`${BASE}/api/v1/pipeline/jobs/${jobId}`).then((r) => r.json()),

  getPipelineResults: (jobId: string) =>
    fetch(`${BASE}/api/v1/pipeline/results/${jobId}`).then((r) => r.json()),

  // ── Notifications ────────────────────────────────────────────────────────

  getNotifications: (unreadOnly = false) =>
    fetch(
      `${BASE}/api/v1/notifications${unreadOnly ? "?unread_only=true" : ""}`,
    ).then((r) => r.json()),

  getUnreadCount: () =>
    fetch(`${BASE}/api/v1/notifications/unread-count`).then((r) => r.json()),

  markNotificationRead: (id: string) =>
    fetch(`${BASE}/api/v1/notifications/${id}/read`, {
      method: "POST",
    }).then((r) => r.json()),

  markAllNotificationsRead: () =>
    fetch(`${BASE}/api/v1/notifications/read-all`, {
      method: "POST",
    }).then((r) => r.json()),

  getNotificationPreferences: () =>
    fetch(`${BASE}/api/v1/notifications/preferences`).then((r) => r.json()),

  updateNotificationPreferences: (prefs: {
    in_app_enabled: boolean;
    email_enabled: boolean;
  }) =>
    fetch(`${BASE}/api/v1/notifications/preferences`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    }).then((r) => r.json()),

  // SSE stream URL (not a fetch — used by EventSource)
  notificationStreamUrl: () => `${BASE}/api/v1/notifications/stream`,
};
