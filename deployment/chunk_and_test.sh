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
python3 chunker.py chunk-and-vectorise \
  "$PROJECT_ROOT" "$PATTERN" \
  --language "$LANGUAGE" \
  --chroma-host "$CHROMA_HOST" \
  --chroma-port "$CHROMA_PORT"

# Run test/query
echo "Testing if file was chunked..."
RESULT=$(python3 chunker.py vectorcode-cli query "$TEST_FILE" --include chunk --chroma-host "$CHROMA_HOST" --chroma-port "$CHROMA_PORT")

if echo "$RESULT" | grep -q "$PROJECT_ROOT/$TEST_FILE"; then
  echo "SUCCESS: Found chunks for $PROJECT_ROOT/$TEST_FILE"
  exit 0
else
  echo "FAIL: No chunks found for $PROJECT_ROOT/$TEST_FILE"
  exit 1
fi
