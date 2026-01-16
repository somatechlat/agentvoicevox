# LLM Worker Dockerfile
# Multi-provider LLM inference (OpenAI, Groq, Ollama)
# Runs Django management command: python manage.py run_llm_worker

FROM python:3.12-slim-bookworm AS base

# Create non-root user for security
RUN useradd -m -u 1000 worker
WORKDIR /app

# Create virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (entire backend)
COPY . /app/

# Set ownership
RUN chown -R worker:worker /app

# Switch to non-root user
USER worker

# Environment variables with defaults
ENV REDIS_URL=redis://localhost:6379/0 \
    LLM_DEFAULT_PROVIDER=groq \
    LLM_DEFAULT_MODEL=llama-3.1-70b-versatile \
    LLM_MAX_TOKENS=1024 \
    LLM_TEMPERATURE=0.7 \
    CIRCUIT_BREAKER_THRESHOLD=5 \
    CIRCUIT_BREAKER_TIMEOUT=30 \
    OLLAMA_BASE_URL=http://localhost:11434 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.base

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "from apps.workflows.management.commands.run_llm_worker import LLMWorker; print('OK')" || exit 1

# Run the LLM worker
CMD ["python", "manage.py", "run_llm_worker"]
