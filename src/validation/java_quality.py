import docker, os, tempfile
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class JavaValidator:
    IMAGE = "ai-agent-java:latest"
    def __init__(self):
        self.client = docker.from_env()
    def validate(self, code: str) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "Code.java")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            # Checkstyle isn't installed by default: let's fallback to compilation test
            out = self.run_tool(tmpdir, ["javac", "/code/Code.java"])
            return {"javac": out}
    def run_tool(self, mount_dir, command):
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
