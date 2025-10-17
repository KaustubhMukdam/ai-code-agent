"""
LangGraph Workflow Definition
This is the agent's decision-making graph
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from src.agent.state import CodeAgentState
from src.agent.nodes import AgentNodes
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeGenerationGraph:
    """LangGraph workflow for code generation agent"""
    
    def __init__(self):
        """Initialize the graph with nodes"""
        self.nodes = AgentNodes()
        self.graph = self._build_graph()
        logger.info("LangGraph workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the state graph with nodes and edges"""

        workflow = StateGraph(CodeAgentState)

        # Add nodes
        workflow.add_node("generate_code", self.nodes.generate_code_node)
        workflow.add_node("review_code", self.nodes.review_code_node)
        workflow.add_node("execute_code", self.nodes.execute_code_node)
        workflow.add_node("validate_code", self.nodes.validate_code_node)
        workflow.add_node("generate_document", self.nodes.generate_document_node)

        workflow.set_entry_point("generate_code")

        # Review conditional branch
        def review_outcome(state: CodeAgentState):
            # Safety: If we hit max iterations, force pass to avoid infinite loop
            if state.get("iteration_count", 0) >= state.get("max_iterations", 3):
                logger.warning("Max iterations reached in review loop, forcing pass")
                return "pass"
            
            # Check for PASS in feedback
            feedback = state.get("review_feedback", "")
            if "PASS" in feedback.upper():  # Case-insensitive check
                return "pass"
            return "retry"

        workflow.add_edge("generate_code", "review_code")

        workflow.add_conditional_edges(
            "review_code",
            review_outcome,
            {
                "retry": "generate_code",
                "pass": "execute_code"
            }
        )

        workflow.add_edge("execute_code", "validate_code")
        workflow.add_edge("validate_code", "generate_document")
        workflow.add_edge("generate_document", END)

        # Validation node conditional (for retries/max)
        workflow.add_conditional_edges(
            "validate_code",
            self.should_retry,
            {
                "retry": "generate_code",
                "complete": "generate_document"
            }
        )

        logger.info("Graph structure built with 5 nodes")

        return workflow
    
    def compile(self):
        """Compile the graph for execution"""
        compiled = self.graph.compile()
        logger.info("Graph compiled successfully")
        return compiled
    
    def should_retry(self, state: CodeAgentState):
        if state["validation_passed"]:
            logger.info("Validation passed - proceeding to documentation")
            return "complete"
        if state["iteration_count"] >= state["max_iterations"]:
            logger.warning("Max iterations reached", ...)
            return "complete"
        logger.info("Validation failed - retrying", language=state.get("target_language"), iteration=state.get("iteration_count"))
        return "retry"


