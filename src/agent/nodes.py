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
from src.utils.docgen import generate_assignment_docx

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

        if state["iteration_count"] > 0 and state.get("review_feedback"):
                prompt += f"\nCode Review Feedback: {state['review_feedback']}\nPlease fix ALL the issues and try again.\n"
        
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
    
    def review_code_node(self, state: CodeAgentState) -> Dict[str, Any]:
        reviewer = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.2,
            max_tokens=2048
        )
        
        requirements = state.get('requirements', 'No explicit requirements provided')
        
        review_prompt = f"""
    You are a strict code reviewer for student programming assignments.

    Original Question:
    {state['problem_description']}

    Requirements (MUST follow exactly):
    {requirements}

    Generated Code:
    {state['generated_code']}

    Execution Output:
    {state.get('execution_output', 'Code not executed yet')}

    Task:
    Review the code and check if it:
    1. Solves the problem correctly
    2. Follows ALL the requirements listed above
    3. Produces correct output

    If the code meets all requirements and works correctly, respond with ONLY the word: PASS

    If there are issues, list them briefly and clearly.
    """
        
        review_result = reviewer.invoke(review_prompt)
        
        if hasattr(review_result, 'content'):
            feedback = review_result.content
        else:
            feedback = str(review_result)
        
        logger.info(f"Review feedback: {feedback[:200]}...")  # Log for debugging
        
        return {
            **state,
            "review_feedback": feedback
        }


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

    
    def validate_code_node(self, state: 'CodeAgentState') -> dict:
        """
        Multi-language validation node.
        Automatically runs language-appropriate quality/security tools,
        aggregates errors, and formats feedback for the agent.
        """
        lang = state["target_language"]
        code = state["generated_code"]
        errors = []         # List of error/warning strings
        details = {}        # Dict {tool: raw_output}

        try:
            if lang == "python":
                from src.validation.quality import PythonValidator
                validator = PythonValidator()
                details = validator.validate(code)
                # Collect errors from pylint, flake8, bandit, black
                for tool in ["pylint", "flake8", "bandit", "black"]:
                    out = details.get(tool, "")
                    if out and "Error" in out or "warning" in out.lower() or "issue" in out.lower():
                        errors.append(f"{tool}: {out.strip()[:200]}") # add first 200 chars for brevity

            elif lang == "javascript":
                from src.validation.js_quality import JavaScriptValidator
                validator = JavaScriptValidator()
                details = validator.validate(code)
                out = details.get("eslint", "")
                if out and ("error" in out.lower() or "problem" in out.lower() or "warning" in out.lower()):
                    errors.append(f"eslint: {out.strip()[:200]}")

            elif lang == "java":
                from src.validation.java_quality import JavaValidator
                validator = JavaValidator()
                details = validator.validate(code)
                out = details.get("javac", "")
                if out and ("error" in out.lower() or "exception" in out.lower()):
                    errors.append(f"javac: {out.strip()[:200]}")

            elif lang == "c":
                from src.validation.c_quality import CValidator
                validator = CValidator()
                details = validator.validate(code)
                for tool in ["cppcheck", "gcc"]:
                    out = details.get(tool, "")
                    if out and ("error" in out.lower() or "failed" in out.lower() or "warning" in out.lower()):
                        errors.append(f"{tool}: {out.strip()[:200]}")

            elif lang == "cpp":
                from src.validation.cpp_quality import CppValidator
                validator = CppValidator()
                details = validator.validate(code)
                for tool in ["cppcheck", "g++"]:
                    out = details.get(tool, "")
                    if out and ("error" in out.lower() or "failed" in out.lower() or "warning" in out.lower()):
                        errors.append(f"{tool}: {out.strip()[:200]}")

            elif lang == "go":
                from src.validation.go_quality import GoValidator
                validator = GoValidator()
                details = validator.validate(code)
                for tool in ["govet", "gobuild"]:
                    out = details.get(tool, "")
                    if out and ("error" in out.lower() or "fail" in out.lower() or "warning" in out.lower()):
                        errors.append(f"{tool}: {out.strip()[:200]}")

            else:
                errors.append(f"Unsupported language: {lang}")

        except Exception as e:
            logger.error(
                "Validation failed for language.",
                language=lang,
                error=str(e),
                code=code[:200] if code else ""
            )
            errors.append(f"Validation engine error: {str(e)}")

        validation_passed = (len(errors) == 0)

        # Add additional metadata flags for agent
        feedback = "\n".join(errors) if errors else "No issues detected."
        # (later you can parse tool outputs more deeply here)
        return {
            "validation_passed": validation_passed,
            "validation_errors": errors,
            "validation_details": details,
            "functional_valid": validation_passed,
            "security_valid": validation_passed,    # placeholder/expand later
            "quality_valid": validation_passed,
            "performance_valid": True,              # placeholder for now
            "status": "completed" if validation_passed else "failed",
            "current_feedback": feedback,
            "feedback_history": state.get("feedback_history", []) + ([feedback] if feedback else []),
            "iteration_count": state.get("iteration_count", 0) + 1,
        }
    
    def generate_document_node(self, state: 'CodeAgentState') -> dict:
        # This is a placeholder! Batch document is generated in the driver.
        logger.info("Documentation node placeholder executed.")
        return {**state, "docx_filename": None, "final_success": True, "status": "completed"}



