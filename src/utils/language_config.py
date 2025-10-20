"""
Advanced language configurations
"""
from dataclasses import dataclass
from typing import List

@dataclass
class LanguageConfig:
    name: str
    extension: str
    docker_image: str
    compile_command: str
    run_command: str
    timeout: int
    memory_limit: str
    supported_frameworks: List[str]

LANGUAGE_CONFIGS = {
    "python": LanguageConfig(
        name="Python",
        extension=".py",
        docker_image="python:3.11-slim",
        compile_command="python -m py_compile {filename}",
        run_command="python {filename}",
        timeout=30,
        memory_limit="256m",
        supported_frameworks=["numpy", "pandas", "matplotlib", "sklearn"]
    ),
    "cpp": LanguageConfig(
        name="C++",
        extension=".cpp",
        docker_image="gcc:latest",
        compile_command="g++ -std=c++17 -Wall -O2 {filename} -o solution",
        run_command="./solution",
        timeout=10,
        memory_limit="128m",
        supported_frameworks=["STL", "iostream", "vector"]
    ),
    "java": LanguageConfig(
        name="Java",
        extension=".java",
        docker_image="openjdk:17-slim",
        compile_command="javac {filename}",
        run_command="java Solution",
        timeout=15,
        memory_limit="512m",
        supported_frameworks=["Collections", "Stream API"]
    ),
    "javascript": LanguageConfig(
        name="JavaScript",
        extension=".js",
        docker_image="node:18-slim",
        compile_command="node --check {filename}",
        run_command="node {filename}",
        timeout=20,
        memory_limit="256m",
        supported_frameworks=["ES2022", "Node.js"]
    )
}

def get_language_config(language: str) -> LanguageConfig:
    return LANGUAGE_CONFIGS.get(language.lower(), LANGUAGE_CONFIGS["python"])

def get_supported_languages() -> List[str]:
    return list(LANGUAGE_CONFIGS.keys())
