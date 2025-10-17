"""
Python code quality validation: pylint, flake8, black, bandit
"""

import docker
import os
import tempfile
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class PythonValidator:
    """
    Runs quality and security tools (pylint, flake8, bandit) in isolated Docker
    """
    IMAGE = "ai-agent-python:latest"

    def __init__(self):
        self.client = docker.from_env()
    
    def validate(self, code: str) -> dict:
        """
        Validate with multiple tools and collect errors/warnings
        """
        results = {}
        tools = {
            "pylint": ["pylint", "--disable=all", "--enable=E,W,F,C", "/code/code.py"],
            "flake8": ["flake8", "/code/code.py", "--max-line-length=120"],
            "bandit": ["bandit", "-r", "/code"],
            "black": ["black", "--check", "/code/code.py"],
        }
        # Create temp code file
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "code.py")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            results = {}
            for tool, command in tools.items():
                try:
                    output = self.run_tool(tmpdir, command)
                    results[tool] = output
                except Exception as e:
                    results[tool] = f"Error running {tool}: {e}"
        return results

    def run_tool(self, mount_dir, command):
        """
        Run a tool inside the Docker container
        """
        container = self.client.containers.run(
            self.IMAGE,
            command,
            volumes={mount_dir: {"bind": "/code", "mode": "rw"}},
            working_dir="/code",
            network_disabled=True,
            mem_limit=settings.docker_memory_limit,
            cpu_quota=settings.docker_cpu_limit * 100000,
            cpu_period=100000,
            detach=True,
            stderr=True,
            stdout=True,
            remove=True
        )
        return container.logs(stdout=True, stderr=True).decode("utf-8")
