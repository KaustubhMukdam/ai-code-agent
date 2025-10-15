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
        
        # Create graph
        workflow = StateGraph(CodeAgentState)
        
        # Add nodes
        workflow.add_node("generate_code", self.nodes.generate_code_node)
        workflow.add_node("execute_code", self.nodes.execute_code_node)
        workflow.add_node("validate_code", self.nodes.placeholder_validate_node)
        workflow.add_node("generate_document", self.nodes.placeholder_document_node)
        
        # Set entry point
        workflow.set_entry_point("generate_code")
        
        # Add edges (linear flow for now, we'll add conditional logic later)
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_edge("execute_code", "validate_code")
        workflow.add_edge("validate_code", "generate_document")
        workflow.add_edge("generate_document", END)
        
        logger.info("Graph structure built with 4 nodes")
        
        return workflow
    
    def compile(self):
        """Compile the graph for execution"""
        compiled = self.graph.compile()
        logger.info("Graph compiled successfully")
        return compiled
    
    def should_retry(self, state: CodeAgentState) -> Literal["generate_code", "generate_document"]:
        """
        Decision function: Should we retry code generation?
        
        Returns:
            - "generate_code" if we should retry
            - "generate_document" if we should finish
        """
        
        # If validation passed, go to document generation
        if state["validation_passed"]:
            logger.info("Validation passed - proceeding to documentation")
            return "generate_document"
        
        # If we've hit max iterations, save and finish
        if state["iteration_count"] >= state["max_iterations"]:
            logger.warning(
                "Max iterations reached",
                iteration_count=state["iteration_count"],
                max_iterations=state["max_iterations"],
            )
            return "generate_document"
        
        # Otherwise, retry
        logger.info(
            "Validation failed - retrying",
            iteration=state["iteration_count"],
            errors=state["validation_errors"],
        )
        return "generate_code"
