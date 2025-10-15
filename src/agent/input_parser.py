"""
Input File Parser
Reads .txt files and extracts problem description + target language
"""

import re
from pathlib import Path
from typing import Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InputParser:
    """Parse input .txt files for code generation"""
    
    LANGUAGE_PATTERNS = [
        r"language:\s*(\w+)",
        r"programming language:\s*(\w+)",
        r"use\s+(\w+)",
        r"write\s+in\s+(\w+)",
        r"code\s+in\s+(\w+)",
    ]
    
    SUPPORTED_LANGUAGES = {
        "python": "python",
        "py": "python",
        "javascript": "javascript",
        "js": "javascript",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "c++": "cpp",
        "go": "go",
        "golang": "go",
    }
    
    @classmethod
    def parse_file(cls, file_path: str) -> Tuple[str, str]:
        """
        Parse input file to extract problem description and language
        
        Expected format:
        ```
        Language: Python
        
        Problem:
        Write a function to calculate fibonacci numbers
        ```
        
        Or simple format:
        ```
        Python
        Calculate fibonacci numbers
        ```
        
        Args:
            file_path: Path to .txt file
            
        Returns:
            Tuple of (problem_description, language)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If language not specified or unsupported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        # Read file content
        content = path.read_text(encoding="utf-8").strip()
        
        if not content:
            raise ValueError("Input file is empty")
        
        logger.info("Parsing input file", file_path=file_path)
        
        # Try to extract language using patterns
        language = cls._extract_language(content)
        
        # Extract problem description (remove language declaration)
        problem = cls._extract_problem(content, language)
        
        # Normalize language name
        language_normalized = cls.SUPPORTED_LANGUAGES.get(language.lower())
        
        if not language_normalized:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(set(cls.SUPPORTED_LANGUAGES.values()))}"
            )
        
        logger.info(
            "Successfully parsed input",
            language=language_normalized,
            problem_length=len(problem),
        )
        
        return problem, language_normalized
    
    @classmethod
    def _extract_language(cls, content: str) -> str:
        """Extract programming language from content"""
        
        # Try all patterns
        for pattern in cls.LANGUAGE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try first line as language
        first_line = content.split("\n")[0].strip()
        if first_line.lower() in cls.SUPPORTED_LANGUAGES:
            return first_line
        
        raise ValueError(
            "Could not detect programming language. "
            "Please specify language using 'Language: Python' format"
        )
    
    @classmethod
    def _extract_problem(cls, content: str, language: str) -> str:
        """Extract problem description by removing language declaration"""
        
        # Remove language line
        lines = content.split("\n")
        problem_lines = []
        
        language_found = False
        for line in lines:
            # Skip language declaration line
            if not language_found and language.lower() in line.lower():
                language_found = True
                continue
            
            # Skip "Problem:" header
            if line.strip().lower() in ["problem:", "problem", "task:", "task"]:
                continue
            
            problem_lines.append(line)
        
        problem = "\n".join(problem_lines).strip()
        
        if not problem:
            raise ValueError("Problem description is empty")
        
        return problem
    
    @classmethod
    def validate_input_format(cls, file_path: str) -> bool:
        """
        Validate if input file has correct format
        
        Returns:
            True if valid, False otherwise
        """
        try:
            cls.parse_file(file_path)
            return True
        except Exception as e:
            logger.error("Input validation failed", error=str(e))
            return False
