FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.13.8

COPY pyproject.toml README.md ./
RUN uv sync --no-dev --no-install-project --no-cache

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
