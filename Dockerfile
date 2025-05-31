FROM python:3.11-slim
WORKDIR /app
RUN apt-get update -qq && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
# Copy pyproject for dependency install
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip \
 && pip install poetry==1.8.2 \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-root
# Copy source code
COPY src src
ENV TZ=America/New_York
ENV PYTHONPATH=/app/src
CMD ["python","-m","phoenix_trader"]
