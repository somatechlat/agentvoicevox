# TTS Worker Dockerfile
# Text-to-Speech synthesis using Kokoro ONNX
# Runs Django management command: python manage.py run_tts_worker

FROM python:3.12-slim-bookworm AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

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

# Create cache directory for models
RUN mkdir -p /app/cache/kokoro && chown -R worker:worker /app

# Switch to non-root user
USER worker

# Environment variables with defaults
ENV REDIS_URL=redis://localhost:6379/0 \
    KOKORO_MODEL_DIR=/app/cache/kokoro \
    KOKORO_MODEL_FILE=kokoro-v1.0.onnx \
    KOKORO_VOICES_FILE=voices-v1.0.bin \
    TTS_DEFAULT_VOICE=am_onyx \
    TTS_DEFAULT_SPEED=1.1 \
    TTS_CHUNK_SIZE=24000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.base

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "from apps.workflows.management.commands.run_tts_worker import TTSWorker; print('OK')" || exit 1

# Run the TTS worker
CMD ["python", "manage.py", "run_tts_worker"]
