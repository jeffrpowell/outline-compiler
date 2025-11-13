# Docker Usage Guide

## Building the Image

```bash
docker build -t outline-compiler .
```

## Running the Container

### Basic Usage

Run the compiler for a specific collection:

```bash
docker run --rm \
  -e OUTLINE_API_KEY="your_api_key_here" \
  -e OUTLINE_COLLECTION_ID="collection_uuid_here" \
  -v $(pwd)/output:/app/output \
  outline-compiler
```

### With Custom API URL (Self-Hosted Outline)

```bash
docker run --rm \
  -e OUTLINE_API_URL="https://your-outline-instance.com/api" \
  -e OUTLINE_API_KEY="your_api_key_here" \
  -e OUTLINE_COLLECTION_ID="collection_uuid_here" \
  -v $(pwd)/output:/app/output \
  outline-compiler
```

### With Custom Output Filename

```bash
docker run --rm \
  -e OUTLINE_API_KEY="your_api_key_here" \
  -e OUTLINE_COLLECTION_ID="collection_uuid_here" \
  -e OUTLINE_OUTPUT_FILE="/app/output/my-compilation.html" \
  -v $(pwd)/output:/app/output \
  outline-compiler
```

## Cron Job Setup

### Using Environment File

1. Create an environment file for each collection (e.g., `collection1.env`):

```bash
# collection1.env
OUTLINE_API_KEY=your_api_key_here
OUTLINE_COLLECTION_ID=collection_uuid_1
OUTLINE_OUTPUT_FILE=/app/output/collection1.html
```

2. Add to your crontab (`crontab -e`):

```cron
# Run every day at 2 AM
0 2 * * * docker run --rm --env-file /path/to/collection1.env -v /path/to/output:/app/output outline-compiler

# Run every 6 hours for another collection
0 */6 * * * docker run --rm --env-file /path/to/collection2.env -v /path/to/output:/app/output outline-compiler
```

### Using Inline Environment Variables

```cron
# Collection 1 - Daily at 2 AM
0 2 * * * docker run --rm -e OUTLINE_API_KEY="key" -e OUTLINE_COLLECTION_ID="uuid1" -v /path/to/output:/app/output outline-compiler

# Collection 2 - Daily at 3 AM
0 3 * * * docker run --rm -e OUTLINE_API_KEY="key" -e OUTLINE_COLLECTION_ID="uuid2" -v /path/to/output:/app/output outline-compiler
```

## Environment Variables

### Required

- `OUTLINE_API_KEY`: Your Outline API key (get from Settings → API & Apps)
- `OUTLINE_COLLECTION_ID`: UUID of the collection to compile

### Optional

- `OUTLINE_API_URL`: Outline API URL (default: `https://app.getoutline.com/api`)
- `OUTLINE_OUTPUT_FILE`: Output file path inside container (default: `/app/output/compilation.html`)

## Volume Mounts

Mount the `/app/output` directory to persist the compiled HTML and attachments:

```bash
-v /host/path/to/output:/app/output
```

The output will contain:
- `index.html` or your specified output filename
- `attachments/` directory (if the documents contain images/files)

## Examples

### Multiple Collections with Separate Output Directories

```bash
# Collection 1
docker run --rm \
  -e OUTLINE_API_KEY="your_api_key" \
  -e OUTLINE_COLLECTION_ID="uuid1" \
  -v $(pwd)/output/docs:/app/output \
  outline-compiler

# Collection 2
docker run --rm \
  -e OUTLINE_API_KEY="your_api_key" \
  -e OUTLINE_COLLECTION_ID="uuid2" \
  -v $(pwd)/output/wiki:/app/output \
  outline-compiler
```

### Using Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  compile-collection1:
    image: outline-compiler
    environment:
      OUTLINE_API_KEY: ${OUTLINE_API_KEY}
      OUTLINE_COLLECTION_ID: collection_uuid_1
      OUTLINE_OUTPUT_FILE: /app/output/collection1.html
    volumes:
      - ./output:/app/output

  compile-collection2:
    image: outline-compiler
    environment:
      OUTLINE_API_KEY: ${OUTLINE_API_KEY}
      OUTLINE_COLLECTION_ID: collection_uuid_2
      OUTLINE_OUTPUT_FILE: /app/output/collection2.html
    volumes:
      - ./output:/app/output
```

Run manually:
```bash
docker compose run --rm compile-collection1
docker compose run --rm compile-collection2
```

## Security Notes

- Never hardcode your API key in the Dockerfile or commit it to version control
- Use environment files with restricted permissions (e.g., `chmod 600 *.env`)
- Consider using Docker secrets or a secret management system for production use
- The compiled output may contain sensitive information - secure your output directory appropriately
