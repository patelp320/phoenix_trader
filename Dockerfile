FROM python:3.11-slim
WORKDIR /app
# Copy pyproject for dependency install
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip \
 && pip install poetry==1.8.2 \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-root
# Copy source code
COPY src src
ENV TZ=America/New_York
CMD ["python","-m","phoenix_trader"]
