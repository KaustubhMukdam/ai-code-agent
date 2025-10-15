FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Install security tools
RUN pip install --no-cache-dir bandit pylint flake8

# Security: Run as non-root user
RUN useradd -m -u 1000 coderunner
USER coderunner

# Default command
CMD ["python"]
