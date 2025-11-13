FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the compiler script and entrypoint
COPY outline_compiler.py .
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Create output directory
RUN mkdir -p /app/output

# Set environment variables with defaults
ENV OUTLINE_API_URL=https://app.getoutline.com/api \
    OUTLINE_OUTPUT_FILE=/app/output/compilation.html

# The collection ID and API key must be provided at runtime
ENV OUTLINE_COLLECTION_ID="" \
    OUTLINE_API_KEY=""

# Run the entrypoint script when container starts
ENTRYPOINT ["/app/docker-entrypoint.sh"]
