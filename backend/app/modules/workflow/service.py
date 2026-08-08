from app.modules.workflow.service_pipeline import PipelineWorkflowService, pipeline_workflow_service
from app.modules.workflow.service_agent import AgentWorkflowService

# Keep workflow_service name for backward compat (= pipeline_workflow_service)
workflow_service = pipeline_workflow_service

__all__ = [
    "PipelineWorkflowService",
    "pipeline_workflow_service",
    "AgentWorkflowService",
    "workflow_service",
]
