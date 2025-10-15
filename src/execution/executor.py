"""
Code Execution Engine
Executes code in isolated Docker containers with security and resource limits
"""

import docker
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
import time
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class CodeExecutor:
    """Execute code in Docker containers with security sandboxing"""
    
    # Map languages to Docker images
    IMAGE_MAP = {
        "python": "ai-agent-python:latest",
        "javascript": "ai-agent-javascript:latest",
        "java": "ai-agent-java:latest",
        "c": "ai-agent-c:latest",
        "cpp": "ai-agent-cpp:latest",
        "go": "golang:1.21-alpine",
    }
    
    # File extensions for each language
    FILE_EXTENSIONS = {
        "python": ".py",
        "javascript": ".js",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "go": ".go",
    }
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Docker client", error=str(e))
            raise RuntimeError(
                "Docker is not available. Please install Docker Desktop: "
                "https://www.docker.com/products/docker-desktop/"
            )
    
    def execute_code(
        self,
        code: str,
        language: str,
        timeout: int = None
    ) -> Dict[str, any]:
        """
        Execute code in a Docker container
        
        Args:
            code: Source code to execute
            language: Programming language (python, javascript, etc.)
            timeout: Maximum execution time in seconds
            
        Returns:
            Dict with:
                - success (bool): Whether execution succeeded
                - output (str): Standard output
                - error (str): Error output
                - exit_code (int): Process exit code
                - execution_time_ms (float): Execution time in milliseconds
        """
        if timeout is None:
            timeout = settings.code_timeout_seconds
        
        language = language.lower()
        
        if language not in self.IMAGE_MAP:
            return {
                "success": False,
                "output": "",
                "error": f"Unsupported language: {language}",
                "exit_code": -1,
                "execution_time_ms": 0.0,
            }
        
        logger.info(
            "Executing code",
            language=language,
            code_length=len(code),
            timeout=timeout,
        )
        
        try:
            # Create temporary file with code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=self.FILE_EXTENSIONS[language],
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute based on language
                result = self._execute_in_container(
                    temp_file,
                    language,
                    timeout
                )
                return result
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error("Code execution failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "exit_code": -1,
                "execution_time_ms": 0.0,
            }
    
    def _execute_in_container(
        self,
        file_path: str,
        language: str,
        timeout: int
    ) -> Dict[str, any]:
        """Execute code file in Docker container"""
        
        image = self.IMAGE_MAP[language]
        file_name = os.path.basename(file_path)
        
        # Build execution command based on language
        command = self._build_command(language, file_name)
        
        # Container configuration
        container_config = {
            "image": image,
            "command": command,
            "volumes": {
                os.path.dirname(file_path): {
                    "bind": "/code",
                    "mode": "ro"  # Read-only
                }
            },
            "working_dir": "/code",
            "detach": True,
            "network_disabled": True,  # No network access
            "mem_limit": settings.docker_memory_limit,
            "cpu_quota": settings.docker_cpu_limit * 100000,
            "cpu_period": 100000,
            "remove": False,  # Changed: Don't auto-remove so we can get logs
        }
        
        start_time = time.time()
        container = None
        
        try:
            # Run container
            container = self.client.containers.run(**container_config)
            
            # Wait for completion with timeout
            result = container.wait(timeout=timeout)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Get logs before removing container
            output = container.logs(stdout=True, stderr=False).decode('utf-8')
            error = container.logs(stdout=False, stderr=True).decode('utf-8')
            exit_code = result['StatusCode']
            
            success = exit_code == 0
            
            logger.info(
                "Code execution completed",
                language=language,
                exit_code=exit_code,
                elapsed_ms=round(elapsed_ms, 2),
                success=success,
            )
            
            return {
                "success": success,
                "output": output.strip(),
                "error": error.strip() if error else "",
                "exit_code": exit_code,
                "execution_time_ms": round(elapsed_ms, 2),
            }
            
        except docker.errors.ContainerError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.warning(
                "Container execution error",
                exit_code=e.exit_status,
                stderr=e.stderr.decode('utf-8') if e.stderr else "",
            )
            return {
                "success": False,
                "output": "",
                "error": e.stderr.decode('utf-8') if e.stderr else str(e),
                "exit_code": e.exit_status,
                "execution_time_ms": round(elapsed_ms, 2),
            }
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error("Container execution failed", error=str(e))
            
            # Handle timeout
            if "timeout" in str(e).lower():
                return {
                    "success": False,
                    "output": "",
                    "error": f"Execution timeout after {timeout} seconds",
                    "exit_code": -1,
                    "execution_time_ms": round(elapsed_ms, 2),
                }
            
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "execution_time_ms": round(elapsed_ms, 2),
            }
        
        finally:
            # Clean up container
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

    
    def _build_command(self, language: str, file_name: str) -> list:
        """Build execution command for each language"""
        
        commands = {
            "python": ["python", f"/code/{file_name}"],
            "javascript": ["node", f"/code/{file_name}"],
            "java": self._build_java_command(file_name),
            "c": self._build_c_command(file_name),
            "cpp": self._build_cpp_command(file_name),
            "go": ["go", "run", f"/code/{file_name}"],
        }
        
        return commands.get(language, [])
    
    def _build_java_command(self, file_name: str) -> list:
        """Build Java compile + run command"""
        class_name = file_name.replace('.java', '')
        return [
            "/bin/sh", "-c",
            f"javac /code/{file_name} && java -cp /code {class_name}"
        ]
    
    def _build_c_command(self, file_name: str) -> list:
        """Build C compile + run command"""
        return [
            "/bin/sh", "-c",
            f"gcc /code/{file_name} -o /tmp/program && /tmp/program"
        ]
    
    def _build_cpp_command(self, file_name: str) -> list:
        """Build C++ compile + run command"""
        return [
            "/bin/sh", "-c",
            f"g++ /code/{file_name} -o /tmp/program && /tmp/program"
        ]
    
    def check_docker_available(self) -> bool:
        """Check if Docker is running"""
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def check_images_available(self) -> Dict[str, bool]:
        """Check which Docker images are available"""
        results = {}
        for language, image in self.IMAGE_MAP.items():
            try:
                self.client.images.get(image)
                results[language] = True
            except:
                results[language] = False
        return results
