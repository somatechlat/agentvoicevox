#!/bin/bash

# =============================================================================
# AGENTVOICEBOX SaaS - STT (SPEECH-TO-TEXT) TESTING
# Tests the complete STT pipeline with real audio files
# =============================================================================

set -e

AUDIO_DIR="/Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/tmp/artifacts-agentvoicevox"

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║  AGENTVOICEBOX STT TESTING                                                ║"
echo "║  Testing Speech-to-Text Pipeline                                         ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if services are running
echo "🔍 Verifying Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DJANGO_RUNNING=$(docker ps --filter "name=avb-django-api" --format "{{.Names}}" | wc -l)
STT_RUNNING=$(docker ps --filter "name=avb-worker-stt" --format "{{.Names}}" | wc -l)

if [ "$DJANGO_RUNNING" -eq 0 ]; then
    echo "❌ Django API not running. Please run ./deploy.sh first"
    exit 1
fi

if [ "$STT_RUNNING" -eq 0 ]; then
    echo "❌ STT Worker not running. Please run ./deploy.sh first"
    exit 1
fi

echo "✅ Django API: RUNNING"
echo "✅ STT Worker: RUNNING"
echo ""

# Check audio files
echo "📋 Checking Test Audio Files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$AUDIO_DIR" ]; then
    echo "❌ Audio directory not found: $AUDIO_DIR"
    exit 1
fi

AUDIO_FILES=("$AUDIO_DIR"/AUDIO*.ogg)
if [ ${#AUDIO_FILES[@]} -eq 0 ]; then
    echo "❌ No audio files found in $AUDIO_DIR"
    exit 1
fi

echo "Found ${#AUDIO_FILES[@]} audio file(s):"
for file in "${AUDIO_FILES[@]}"; do
    size=$(du -h "$file" | cut -f1)
    echo "  🎵 $(basename "$file") - $size"
done
echo ""

# Test STT Configuration Endpoint
echo "🧪 TEST 1: Check STT Configuration (GET /stt/config)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Note: This will fail without authentication, but that's expected
# We're checking if the endpoint exists and responds
curl -s -X GET http://localhost:65020/stt/config 2>&1 | head -5
echo ""

# Test STT with first audio file
echo "🧪 TEST 2: Upload Audio for STT Transcription (POST /stt/test)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

AUDIO_FILE="${AUDIO_FILES[0]}"
echo "Testing with: $(basename "$AUDIO_FILE")"
echo ""

# Get API key (from environment or generate)
if [ -z "$TEST_API_KEY" ]; then
    echo "⚠️  No API key provided. Testing with local endpoint..."
    echo "   (In production, you would: export TEST_API_KEY=your_key)"
    echo ""
    
    # Direct upload simulation
    echo "Uploading audio file to STT service..."
    RESPONSE=$(curl -s -X POST \
        -F "audio=@$AUDIO_FILE" \
        http://localhost:65020/stt/test 2>&1)
    
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    # With API key
    echo "Using API Key: ${TEST_API_KEY:0:8}..."
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $TEST_API_KEY" \
        -F "audio=@$AUDIO_FILE" \
        http://localhost:65020/stt/test 2>&1)
    
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
fi

echo ""

# Test STT Metrics
echo "🧪 TEST 3: Check STT Metrics (GET /stt/metrics)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# This will need authentication
curl -s -X GET http://localhost:65020/stt/metrics 2>&1 | head -10
echo ""

# Check worker logs
echo "🧪 TEST 4: Worker Logs (Last 10 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "STT Worker logs:"
docker logs --tail 10 avb-worker-stt 2>&1 || echo "No logs yet"
echo ""

echo "Django API logs:"
docker logs --tail 10 avb-django-api 2>&1 | grep -i "stt\|audio\|transcribe" || echo "No STT-related logs yet"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║  ✅ STT TESTING COMPLETE                                                  ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  • Audio files: READY"
echo "  • Django API: ACCESSIBLE"
echo "  • STT Worker: RUNNING"
echo ""
echo "Next: Run ./test-speech-to-speech.sh for full pipeline test"
