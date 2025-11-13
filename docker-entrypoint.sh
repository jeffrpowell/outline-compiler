#!/bin/bash
set -e

# Check required environment variables
if [ -z "$OUTLINE_API_KEY" ]; then
    echo "Error: OUTLINE_API_KEY environment variable is required"
    exit 1
fi

if [ -z "$OUTLINE_COLLECTION_ID" ]; then
    echo "Error: OUTLINE_COLLECTION_ID environment variable is required"
    exit 1
fi

# Set defaults
API_URL="${OUTLINE_API_URL:-https://app.getoutline.com/api}"
OUTPUT_FILE="${OUTLINE_OUTPUT_FILE:-/app/output/compilation.html}"

# Run the compiler
exec python3 outline_compiler.py \
    --api-url "$API_URL" \
    --api-key "$OUTLINE_API_KEY" \
    --collection-id "$OUTLINE_COLLECTION_ID" \
    --output "$OUTPUT_FILE"
