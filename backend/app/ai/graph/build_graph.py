"""LangGraph graph assembly (TRD §8.1) — this slice only.

Per plan decision: wires impact_mapping -> sop_generation ->
evidence_implementation_plan -> gate_2 -> (execution_handoff | sop_generation)
for real. The 4 upstream agents (applicability, obligation_extraction,
change_analysis, ambiguity_detection) + gate_1 are owned by other
implementers and still empty stubs — importing them here would break this
file for everyone, so they're left as a commented TODO block below instead.
Entry point is temporarily "impact_mapping"; move it to "applicability" once
upstream lands.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from app.ai.graph.checkpointer import get_checkpointer
from app.ai.graph.deps import NodeDeps
from app.ai.graph.nodes.evidence_implementation_plan_agent import evidence_implementation_plan_agent
from app.ai.graph.nodes.execution_handoff import handoff_to_execution_engine
from app.ai.graph.nodes.human_gate_2 import human_gate_2
from app.ai.graph.nodes.impact_mapping_agent import impact_mapping_agent
from app.ai.graph.nodes.sop_generation_agent import sop_generation_agent
from app.ai.graph.state import WorkflowState
from app.modules.workflow.schemas import GateDecision

# TODO(teammate): once applicability_agent / obligation_extraction_agent /
# change_analysis_agent / ambiguity_detection_agent / human_gate_1 are
# implemented, wire them in like this and move the entry point below:
#
#   graph.add_node("applicability", partial(applicability_agent, deps=deps))
#   graph.add_node("obligation_extraction", partial(obligation_extraction_agent, deps=deps))
#   graph.add_node("change_analysis", partial(change_analysis_agent, deps=deps))
#   graph.add_node("ambiguity_detection", partial(ambiguity_detection_agent, deps=deps))
#   graph.add_node("gate_1", partial(human_gate_1, deps=deps))
#   graph.add_edge("applicability", "obligation_extraction")
#   graph.add_edge("obligation_extraction", "change_analysis")
#   graph.add_edge("change_analysis", "ambiguity_detection")
#   graph.add_edge("ambiguity_detection", "gate_1")
#   graph.add_edge("gate_1", "impact_mapping")
#   graph.set_entry_point("applicability")  # replaces the impact_mapping entry point below


async def _route_after_gate_2(state: WorkflowState, deps: NodeDeps) -> str:
    document = await deps.workflow_service.get_document(state.workflow_id)
    approval = document.swd.human_approvals.get("gate_2")
    if approval is not None and approval.decision == GateDecision.approved:
        return "execution_handoff"
    return "sop_generation"


def build_graph(deps: NodeDeps):
    graph = StateGraph(WorkflowState)

    graph.add_node("impact_mapping", partial(impact_mapping_agent, deps=deps))
    graph.add_node("sop_generation", partial(sop_generation_agent, deps=deps))
    graph.add_node("evidence_implementation_plan", partial(evidence_implementation_plan_agent, deps=deps))
    graph.add_node("gate_2", partial(human_gate_2, deps=deps))
    graph.add_node("execution_handoff", partial(handoff_to_execution_engine, deps=deps))

    graph.add_edge("impact_mapping", "sop_generation")
    graph.add_edge("sop_generation", "evidence_implementation_plan")
    graph.add_edge("evidence_implementation_plan", "gate_2")
    graph.add_conditional_edges(
        "gate_2",
        partial(_route_after_gate_2, deps=deps),
        {"execution_handoff": "execution_handoff", "sop_generation": "sop_generation"},
    )
    graph.add_edge("execution_handoff", END)

    graph.set_entry_point("impact_mapping")  # TODO(teammate): change to "applicability" once upstream lands

    return graph.compile(checkpointer=get_checkpointer())
