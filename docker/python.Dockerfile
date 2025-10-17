FROM python:3.11-slim

WORKDIR /code

# Install all validation tools
RUN pip install --no-cache-dir bandit pylint flake8 black

# Security: Run as non-root user
RUN useradd -m -u 1000 coderunner
USER coderunner

CMD ["python"]
