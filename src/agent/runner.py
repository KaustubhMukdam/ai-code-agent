"""
Batch job runner for API integration
"""
import asyncio
from pathlib import Path
from src.agent.state import create_initial_state
from src.agent.graph import CodeGenerationGraph
from src.agent.input_parser import parse_multi_question_file_with_meta
from src.utils.docgen import generate_assignment_docx
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


def run_batch_job(input_file_path: str, output_dir: str) -> str:
    """
    Run the complete workflow for an assignment file
    
    Args:
        input_file_path: Path to the input .txt file
        output_dir: Directory to save the output .docx
    
    Returns:
        Path to the generated .docx file
    
    Raises:
        Exception: If processing fails
    """
    try:
        # Parse the input file
        meta, questions = parse_multi_question_file_with_meta(input_file_path)
        
        results_for_doc = []
        
        # Process each question
        for q in questions:
            logger.info(f"Processing Question {q['number']}")
            
            # Convert requirements to string
            requirements_str = "\n".join(q["requirements"]) if isinstance(q["requirements"], list) else str(q["requirements"])
            
            # Create initial state
            initial_state = create_initial_state(
                problem_description=q["question"],
                target_language=q["language"],
                requirements=requirements_str,
                input_file_path=input_file_path,
                max_iterations=settings.max_iterations,
            )
            
            # Run the workflow
            graph_builder = CodeGenerationGraph()
            app = graph_builder.compile()
            
            # Run synchronously (API will handle async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            final_state = loop.run_until_complete(app.ainvoke(initial_state))
            loop.close()
            
            # Collect results
            code = final_state.get("generated_code", "")
            output = final_state.get("execution_output", "")
            
            results_for_doc.append({
                "number": q['number'],
                "text": q['question'],
                "code": code,
                "output": output,
            })
        
        # Generate output filename
        output_filename = f"{meta['subject'].replace(' ', '_')}_Assignment_{meta['assignment_number']}.docx"
        output_path = str(Path(output_dir) / output_filename)
        
        # Generate document
        generate_assignment_docx(
            questions=results_for_doc,
            filename=output_path,
            subject_name=meta.get("subject", "Assignment"),
            assignment_number=meta.get("assignment_number", ""),
            student_name=meta.get("name", ""),
            student_class=meta.get("class", ""),
            student_div=meta.get("div", ""),
            student_rollno=meta.get("roll_no", ""),
            student_batch=meta.get("batch", "")
        )
        
        logger.info(f"✅ Assignment complete: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}", exc_info=True)
        raise
    
def test_runner():
    """Test the runner with a sample file"""
    import sys
    from src.utils.logger import setup_logging
    
    # Initialize logging
    setup_logging()
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/input/DS_Sample_automate_input.txt"
    
    try:
        print(f"🚀 Starting job for: {input_file}")
        result = run_batch_job(input_file, "data/output")
        print(f"✅ Success! Document saved to: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
