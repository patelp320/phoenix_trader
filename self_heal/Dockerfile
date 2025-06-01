FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pytest ruff bandit atheris requests && \
    apt-get update && apt-get install -y gh git
CMD ["python", "orchestrator.py"]
