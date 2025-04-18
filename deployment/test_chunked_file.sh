#!/bin/bash
set -e

CHROMA_HOST="${CHROMA_HOST:-vectorcode_chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"
PROJECT_ROOT="/app/deployment/tests/testproject"
TEST_FILE="foo.py"
COLLECTION_NAME="default"  # Change if your collection name is different

# Wait for ChromaDB to be available
echo "Waiting for ChromaDB at $CHROMA_HOST:$CHROMA_PORT..."
for i in {1..30}; do
  if nc -z "$CHROMA_HOST" "$CHROMA_PORT"; then
    echo "ChromaDB is up!"
    break
  fi
  sleep 1
done

# Query ChromaDB for the collection and check for the file
FULL_PATH="$PROJECT_ROOT/$TEST_FILE"

# Get collection id
COLLECTION_ID=$(curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/collections" | jq -r ".collections[] | select(.name==\"$COLLECTION_NAME\") | .id")

if [ -z "$COLLECTION_ID" ]; then
  echo "FAIL: Collection '$COLLECTION_NAME' not found."
  exit 1
fi

# Search for the file in the collection
RESULT=$(curl -s -X POST "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/collections/$COLLECTION_ID/get" \
  -H "Content-Type: application/json" \
  -d "{\"where\": {\"path\": \"$FULL_PATH\"}}" \
)

COUNT=$(echo "$RESULT" | jq '.ids | length')

if [ "$COUNT" -gt 0 ]; then
  echo "SUCCESS: Found $COUNT chunks for $FULL_PATH"
  exit 0
else
  echo "FAIL: No chunks found for $FULL_PATH"
  exit 1
fi
