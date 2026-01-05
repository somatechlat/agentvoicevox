# Kokoro Model Selection

The TTS worker uses Kokoro ONNX and reads the model filename from `KOKORO_MODEL_FILE`.

## Environment Variable

- **`KOKORO_MODEL_FILE`** – ONNX model filename to load from the cache directory (`/app/cache/kokoro`).
  - Default: `kokoro-v1.0.onnx`
  - Example to use a different model:
    ```bash
    export KOKORO_MODEL_FILE=Kokoro-200M.onnx
    ```

The variable is read in these places:

1. **`ovos-voice-agent/AgentVoiceBoxEngine/Dockerfile`** – downloads the model into the cache directory.
2. **`ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/management/commands/run_tts_worker.py`** – loads the model at runtime.

## How to Provide a New Model

1. Place the ONNX model file (e.g., `Kokoro-200M.onnx`) in a location accessible during the Docker build, such as a local cache or volume mount.
2. Set `KOKORO_MODEL_FILE` (and optionally `KOKORO_MODEL_URL`) before building the image.
3. Rebuild the Docker image and restart the stack.

## Rebuilding the Stack

```bash
cd ovos-voice-agent/AgentVoiceBoxEngine

docker compose -p agentvoicebox build --no-cache
docker compose -p agentvoicebox up -d
```

The health endpoint is available at `http://localhost:65020/health/`.

## Verifying the Model

You can check the logs of the TTS worker container to see which model file was loaded.
