# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# install git
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./

RUN python -m pip install --upgrade pip setuptools wheel

# Install third-party deps only (skip the editable self-install for now).
# The cache mount keeps downloaded wheels across builds, so a network
# hiccup only re-fetches what's missing on retry.
RUN --mount=type=cache,target=/root/.cache/pip \
    grep -v '^-e' requirements.txt > /tmp/requirements.no-editable.txt && \
    python -m pip install --prefer-binary --progress-bar off --default-timeout=600 --retries 10 -r /tmp/requirements.no-editable.txt

COPY . .

# Now install the project itself; deps are already present.
RUN python -m pip install --no-deps --no-cache-dir -e .

EXPOSE 8001

# run uvicorn properly on 0.0.0.0:8001
CMD ["bash", "-c", "python prod_assistant/mcp_servers/product_search_server.py & uvicorn prod_assistant.router.main:app --host 0.0.0.0 --port 8001 --workers 2"]
