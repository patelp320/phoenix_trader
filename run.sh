export PYTHONPATH="$PYTHONPATH:/app/devin"

export PYTHONPATH="$PYTHONPATH:/app/devin/agenthub"

#!/usr/bin/env bash
docker compose up -d --build
docker compose logs -f
