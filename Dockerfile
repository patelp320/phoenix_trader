FROM python:3.11-slim

# ---------- basic tooling ----------
RUN apt-get update && apt-get install -y \
        build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

# ---------- poetry ----------
RUN pip install --upgrade pip && pip install poetry

# ---------- Python deps that devin/crew/auto-fix need ----------
RUN pip install --no-cache-dir playwright==1.44.0 json_repair chromadb llama-index litellm tenacity termcolor toml && playwright install --with-deps --silent
        playwright==1.44.0 \
        json-repair chromadb llama-index litellm tenacity termcolor toml && \
    playwright install --with-deps --silent   # headless browsers

# ---------- project code ----------
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root
COPY src src

CMD ["python", "-m", "phoenix_trader"]
