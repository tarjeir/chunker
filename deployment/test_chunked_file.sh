#!/bin/bash
set -e

CHROMA_HOST="${CHROMA_HOST:-vectorcode_chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"
PROJECT_ROOT="/app/deployment/tests/testproject"
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

# Use chunker.py to proxy the query to vectorcode
RESULT=$(python3 chunker.py vectorcode-cli query "$TEST_FILE" --include chunk --chroma-host "$CHROMA_HOST" --chroma-port "$CHROMA_PORT")

# Check if the result contains the file path
if echo "$RESULT" | grep -q "$PROJECT_ROOT/$TEST_FILE"; then
  echo "SUCCESS: Found chunks for $PROJECT_ROOT/$TEST_FILE"
  exit 0
else
  echo "FAIL: No chunks found for $PROJECT_ROOT/$TEST_FILE"
  exit 1
fi
