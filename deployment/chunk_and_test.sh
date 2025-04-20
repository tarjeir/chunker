#!/bin/bash
set -e

CHROMA_HOST="${CHROMA_HOST:-vectorcode_chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"
PROJECT_ROOT="/app/deployment/tests/testproject"
PATTERN="*.py"
LANGUAGE="python"
TEST_FILE="foo.py"

# Wait for ChromaDB to be available
echo "Waiting for ChromaDB at $CHROMA_HOST:$CHROMA_PORT..."
for i in {1..30}; do
  if nc -z "$CHROMA_HOST" "$CHROMA_PORT"; then
    echo "ChromaDB is up!"
    break
  fi
  sleep 1
done

# Run chunking
echo "Running chunking..."
chunker chunk-and-vectorise \
  "$PROJECT_ROOT" "$PATTERN" \
  --language "$LANGUAGE" \
  --chroma-host "$CHROMA_HOST" \
  --chroma-port "$CHROMA_PORT" \
  --collection-name "default" \
  --max-batch-size 64

# Run test/query
echo "Testing if file was chunked..."
RESULT=$(chunker query-chunks \
  "$TEST_FILE" \
  --chroma-host "$CHROMA_HOST" \
  --chroma-port "$CHROMA_PORT" \
  --collection-name "default" \
  --n-results 10)

echo "Query Results:"
echo "$RESULT"

if echo "$RESULT" | grep -q "$TEST_FILE"; then
  echo "SUCCESS: Found chunks for $TEST_FILE"
  exit 0
else
  echo "FAIL: No chunks found for $TEST_FILE"
  exit 1
fi
