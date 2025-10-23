#!/bin/bash
# Helper script to run outline_compiler.py using environment variables
# Usage: ./compile_with_env.sh

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$OUTLINE_API_KEY" ]; then
    echo "Error: OUTLINE_API_KEY environment variable is not set"
    echo "Please create a .env file from .env.example and set your API key"
    exit 1
fi

if [ -z "$OUTLINE_COLLECTION_ID" ]; then
    echo "Error: OUTLINE_COLLECTION_ID environment variable is not set"
    echo "Please set your collection ID in the .env file"
    exit 1
fi

# Set defaults
API_URL="${OUTLINE_API_URL:-https://app.getoutline.com/api}"
OUTPUT_FILE="${OUTLINE_OUTPUT_FILE:-outline_compilation.html}"

# Run the compiler
echo "Compiling Outline collection..."
python3 outline_compiler.py \
    --api-url "$API_URL" \
    --api-key "$OUTLINE_API_KEY" \
    --collection-id "$OUTLINE_COLLECTION_ID" \
    --output "$OUTPUT_FILE"
