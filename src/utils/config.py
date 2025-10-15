"""
Configuration management for AI Code Agent
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-70b-versatile", env="GROQ_MODEL")
    
    # LangSmith (Optional)
    langsmith_api_key: str = Field(default="", env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="ai-code-agent", env="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=False, env="LANGSMITH_TRACING")
    
    # Application
    app_name: str = Field(default="AI-Code-Agent", env="APP_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Execution Limits
    max_iterations: int = Field(default=5, env="MAX_ITERATIONS", ge=1, le=10)
    code_timeout_seconds: int = Field(default=30, env="CODE_TIMEOUT_SECONDS", ge=5, le=300)
    docker_memory_limit: str = Field(default="512m", env="DOCKER_MEMORY_LIMIT")
    docker_cpu_limit: int = Field(default=1, env="DOCKER_CPU_LIMIT")
    
    # Database
    database_url: str = Field(default="sqlite:///./ai_agent.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    enable_security_scan: bool = Field(default=True, env="ENABLE_SECURITY_SCAN")
    allowed_languages: str = Field(default="python,javascript,java,go,cpp", env="ALLOWED_LANGUAGES")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    input_dir: Path = base_dir / "data" / "input"
    output_dir: Path = base_dir / "data" / "output"
    log_dir: Path = base_dir / "logs"
    docker_dir: Path = base_dir / "docker"
    
    @validator("allowed_languages")
    def parse_languages(cls, v):
        """Convert comma-separated string to list"""
        if isinstance(v, str):
            return [lang.strip().lower() for lang in v.split(",")]
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
