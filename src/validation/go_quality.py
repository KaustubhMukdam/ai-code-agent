import docker, os, tempfile
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class GoValidator:
    IMAGE = "golang:1.21-alpine"
    def __init__(self):
        self.client = docker.from_env()
    def validate(self, code: str) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "code.go")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            out1 = self.run_tool(tmpdir, ["go", "vet", "/code/code.go"])
            out2 = self.run_tool(tmpdir, ["go", "build", "/code/code.go"])
            # golint is deprecated, staticcheck can be installed in a custom image
            return {"govet": out1, "gobuild": out2}
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
