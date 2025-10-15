"""
LangGraph Node Functions
Each node is a discrete step in the agent workflow
"""

from typing import Dict, Any
import time
from langchain_groq import ChatGroq
from src.agent.state import CodeAgentState
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AgentNodes:
    """Collection of node functions for the LangGraph workflow"""
    
    def __init__(self):
        """Initialize with LLM client"""
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.2,  # Low temperature for consistent code generation
            max_tokens=4096,
        )
        logger.info(
            "Agent nodes initialized",
            model=settings.groq_model,
        )
    
    def generate_code_node(self, state: CodeAgentState) -> Dict[str, Any]:
        """
        Node 1: Generate code using LLM
        
        This is where the magic happens - the LLM generates code based on:
        - Problem description
        - Target programming language
        - Previous feedback (if any)
        """
        logger.info(
            "Generating code",
            language=state["target_language"],
            iteration=state["iteration_count"] + 1,
        )
        
        # Build the prompt
        prompt = self._build_generation_prompt(state)
        
        # Call LLM
        try:
            start_time = time.time()
            response = self.llm.invoke(prompt)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Get response content (handle different response types)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Extract code from response
            generated_code = self._extract_code_from_response(
                response_text,
                state["target_language"]
            )
            
            # Get token usage safely
            token_usage = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_usage = response.usage_metadata.get("total_tokens", 0)
            
            logger.info(
                "Code generated successfully",
                code_length=len(generated_code),
                elapsed_ms=round(elapsed_ms, 2),
                tokens=token_usage,
            )
            
            # Update state
            return {
                "generated_code": generated_code,
                "code_explanation": response_text,
                "iteration_count": state["iteration_count"] + 1,
                "llm_model_used": settings.groq_model,
                "llm_calls_made": state["llm_calls_made"] + 1,
                "total_tokens_used": state["total_tokens_used"] + token_usage,
                "status": "generating",
            }
            
        except Exception as e:
            logger.error("Code generation failed", error=str(e), exc_info=True)
            return {
                "generated_code": "",
                "error_message": f"Code generation failed: {str(e)}",
                "status": "failed",
            }
    
    def _build_generation_prompt(self, state: CodeAgentState) -> str:
        """Build prompt for code generation"""
        
        language = state["target_language"]
        problem = state["problem_description"]
        
        # Base prompt
        prompt = f"""You are an expert {language.upper()} programmer. Generate clean, production-ready code.

PROBLEM:
{problem}

PROGRAMMING LANGUAGE: {language.upper()}

REQUIREMENTS:
1. Write complete, runnable code
2. Include all necessary imports
3. Add clear comments explaining the logic
4. Handle edge cases and errors
5. Follow {language} best practices and style guidelines
6. Make the code efficient and readable

"""
        
        # Add feedback from previous iterations if any
        if state["iteration_count"] > 0 and state["current_feedback"]:
            prompt += f"""
PREVIOUS ATTEMPT FAILED. FEEDBACK:
{state["current_feedback"]}

IMPORTANT: Fix the issues mentioned above and generate improved code.

"""
        
        prompt += f"""
CRITICAL OUTPUT RULES:
1. DO NOT include markdown code blocks (no ```)
2. DO NOT include language tags like ```
3. DO NOT add any explanations before or after the code
4. START IMMEDIATELY with the first line of actual {language} code
5. END with the last line of actual {language} code

Your response MUST start with actual {language} code, not with ```:
"""        
        return prompt
    
    def _extract_code_from_response(self, response: str, language: str) -> str:
        """
        Extract clean code from LLM response
        Removes markdown code blocks if present
        """
        import re
        
        # Handle if response is a list (convert to string)
        if isinstance(response, list):
            response = "\n".join(str(item) for item in response)
        
        # Convert to string if it's not already
        response = str(response).strip()
        
        # Try multiple patterns to extract code blocks
        patterns = [
            r"```(?:python|javascript|java|cpp?|go)\s*\n(.*?)\n``````python ... ```"
            r"```\s*\n(.*?)\n`````` ... ```"
            r"~~~(?:\w+)?\s*\n(.*?)\n~~~",  # ~~~ ... ~~~
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            if matches:
                # Return the first code block found
                code = matches.strip()
                logger.info("Extracted code from markdown block", pattern=pattern)
                return code
        
        # If no code blocks found, check if response starts with markdown
        if response.startswith("```"):
            # Remove first and last line
            lines = response.split("\n")
            if len(lines) > 2:
                code = "\n".join(lines[1:-1]).strip()
                logger.info("Removed markdown delimiters from response")
                return code
        
        # Last resort: return the whole response stripped
        logger.info("No markdown blocks found, using raw response")
        return response.strip()

    
    def execute_code_node(self, state: CodeAgentState) -> Dict[str, Any]:
        """
        Node 2: Execute code in Docker sandbox
        """
        from src.execution.executor import CodeExecutor
        
        logger.info(
            "Executing code in Docker",
            language=state["target_language"],
            code_length=len(state["generated_code"]),
        )
        
        try:
            executor = CodeExecutor()
            
            # Execute the code
            result = executor.execute_code(
                code=state["generated_code"],
                language=state["target_language"],
                timeout=settings.code_timeout_seconds,
            )
            
            logger.info(
                "Code execution completed",
                success=result["success"],
                exit_code=result["exit_code"],
                elapsed_ms=result["execution_time_ms"],
            )
            
            return {
                "execution_output": result["output"],
                "execution_error": result["error"],
                "execution_success": result["success"],
                "execution_time_ms": result["execution_time_ms"],
                "status": "validating",
            }
            
        except Exception as e:
            logger.error("Execution node failed", error=str(e), exc_info=True)
            return {
                "execution_output": "",
                "execution_error": f"Execution failed: {str(e)}",
                "execution_success": False,
                "execution_time_ms": 0.0,
                "status": "failed",
            }

    
    def placeholder_validate_node(self, state: CodeAgentState) -> Dict[str, Any]:
        """
        Node 3: Validate code quality, security, functionality
        (PLACEHOLDER - We'll implement this in Phase 4)
        """
        logger.info("Validating code (placeholder)")
        
        # For now, just mark as valid
        return {
            "validation_passed": True,
            "validation_errors": [],
            "functional_valid": True,
            "security_valid": True,
            "quality_valid": True,
            "performance_valid": True,
            "validation_details": {"placeholder": True},
            "status": "completed",
        }
    
    def placeholder_document_node(self, state: CodeAgentState) -> Dict[str, Any]:
        """
        Node 4: Generate .docx documentation
        (PLACEHOLDER - We'll implement this in Phase 6)
        """
        logger.info("Generating documentation (placeholder)")
        
        output_path = settings.output_dir / f"output_{state['session_id'][:8]}.docx"
        
        return {
            "output_file_path": str(output_path),
            "final_success": True,
            "end_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "completed",
        }
