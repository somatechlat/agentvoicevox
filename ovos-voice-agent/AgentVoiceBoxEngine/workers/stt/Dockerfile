# STT Worker Dockerfile
# Speech-to-Text transcription using Faster-Whisper
# Runs Django management command: python manage.py run_stt_worker

FROM python:3.12-slim-bookworm AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
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

# Set ownership
RUN chown -R worker:worker /app

# Switch to non-root user
USER worker

# Environment variables with defaults
ENV REDIS_URL=redis://localhost:6379/0 \
    STT_MODEL=base \
    STT_DEVICE=auto \
    STT_COMPUTE_TYPE=float16 \
    STT_BATCH_SIZE=4 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.base

# Health check - verify worker can import and connect
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from apps.workflows.management.commands.run_stt_worker import STTWorker; print('OK')" || exit 1

# Run the STT worker
CMD ["python", "manage.py", "run_stt_worker"]
