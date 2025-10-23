# Outline Document Compiler

A Python tool to compile all documents from an Outline knowledge base collection into a single, viewable HTML file. Documents are traversed and compiled in depth-first search (DFS) order, preserving the hierarchical structure of your documentation.

## Features

- **Single HTML Output**: Generates a standalone HTML file that can be viewed in any web browser without requiring markdown support
- **Depth-First Traversal**: Documents are compiled in depth-first order, maintaining the logical structure of your documentation
- **Full Markdown Support**: Converts markdown content to formatted HTML with support for:
  - Code blocks with syntax highlighting
  - Tables
  - Blockquotes
  - Images
  - Lists and nested lists
  - Links
- **Table of Contents**: Automatically generates a clickable table of contents
- **Document Metadata**: Includes author information and last updated dates
- **Print-Friendly**: Optimized CSS for printing or PDF export from browser
- **Visual Hierarchy**: Indentation and styling reflect the document hierarchy

## Requirements

- Python 3.7 or higher
- Internet connection to access Outline API

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests markdown
```

## Getting Your Outline API Key

1. Log in to your Outline instance
2. Navigate to **Settings → API & Apps**
3. Click **Create API Key**
4. Copy the generated API key (treat it like a password!)
5. Set the appropriate scopes - at minimum you need:
   - `collections:read`
   - `documents:read`

## Finding Your Collection ID

There are several ways to find your collection ID:

### Method 1: From the URL
When viewing a collection in Outline, the URL will look like:
```
https://app.getoutline.com/collection/abc123def456
```
The part after `/collection/` is your collection ID.

### Method 2: Using the API
You can list all collections using curl:
```bash
curl -X POST https://app.getoutline.com/api/collections.list \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## Usage

### Basic Usage (Cloud-Hosted Outline)

```bash
python outline_compiler.py \
  --api-key YOUR_API_KEY \
  --collection-id COLLECTION_UUID
```

This will create `outline_compilation.html` in the current directory.

### Self-Hosted Outline

```bash
python outline_compiler.py \
  --api-url https://outline.example.com/api \
  --api-key YOUR_API_KEY \
  --collection-id COLLECTION_UUID
```

### Custom Output File

```bash
python outline_compiler.py \
  --api-key YOUR_API_KEY \
  --collection-id COLLECTION_UUID \
  --output my_docs.html
```

### Complete Example

```bash
python outline_compiler.py \
  --api-url https://app.getoutline.com/api \
  --api-key sk_test_abc123... \
  --collection-id 550e8400-e29b-41d4-a716-446655440000 \
  --output engineering_docs.html
```

## Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--api-key` | Yes | - | Your Outline API key |
| `--collection-id` | Yes | - | UUID of the collection to compile |
| `--api-url` | No | `https://app.getoutline.com/api` | Outline API base URL |
| `--output` | No | `outline_compilation.html` | Output HTML file path |

## Output Format

The generated HTML file includes:

1. **Header Section**: Collection name and compilation timestamp
2. **Collection Description**: If the collection has a description
3. **Table of Contents**: Hierarchical list of all documents with links
4. **Document Content**: Each document with:
   - Title
   - Author and last updated date
   - Full content converted from markdown
   - Visual indentation based on hierarchy level

## Viewing the Output

Simply open the generated HTML file in any web browser:

```bash
# On Linux
xdg-open outline_compilation.html

# On macOS
open outline_compilation.html

# On Windows
start outline_compilation.html
```

## Converting to PDF

To convert the HTML to PDF, you can:

1. **Use your browser**: Open the HTML file and use Print → Save as PDF
2. **Use command-line tools**:

```bash
# Using wkhtmltopdf
wkhtmltopdf outline_compilation.html outline_docs.pdf

# Using weasyprint
weasyprint outline_compilation.html outline_docs.pdf
```

## Security Considerations

⚠️ **Important Security Notes:**

- **Never commit your API key to version control**
- Store your API key securely (e.g., in environment variables or a password manager)
- Use environment variables for sensitive data:

```bash
export OUTLINE_API_KEY="your_api_key_here"
python outline_compiler.py --api-key "$OUTLINE_API_KEY" --collection-id YOUR_COLLECTION_ID
```

- Consider using `.env` files (not tracked in git) for local development
- API keys have the same permissions as your user account - protect them accordingly

## Troubleshooting

### "Unauthenticated" Error
- Check that your API key is correct
- Ensure the API key hasn't been revoked
- Verify the API key has proper scopes (collections:read, documents:read)

### "Not Found" Error
- Verify the collection ID is correct
- Check that your API key has permission to access the collection
- Ensure the collection hasn't been deleted

### "Rate Limited" Error
- Wait a few minutes and try again
- The Outline API has rate limits to prevent abuse
- If repeatedly hitting limits, consider adding delays between requests

### Empty or Missing Content
- Some documents may be drafts or have no content
- Check document permissions - private documents may not be accessible via API
- Verify the documents exist in the Outline UI

### Connection Errors
- Check your internet connection
- Verify the API URL is correct (especially for self-hosted instances)
- Ensure your firewall isn't blocking the connection

## How It Works

1. **Fetch Collection Info**: Retrieves collection metadata (name, description)
2. **Get Document Structure**: Calls `/collections.documents` to get the hierarchical document tree
3. **Depth-First Traversal**: Recursively traverses the document tree in DFS order
4. **Fetch Document Content**: For each document, calls `/documents.info` to get full content
5. **Convert Markdown**: Converts markdown content to HTML
6. **Generate HTML**: Assembles everything into a single, styled HTML file

## API Endpoints Used

This tool uses the following Outline API endpoints:

- `POST /api/collections.info` - Get collection metadata
- `POST /api/collections.documents` - Get collection document structure
- `POST /api/documents.info` - Get individual document content

## Limitations

- Only compiles published documents (drafts are not included)
- Attachments and images are linked, not embedded (requires internet access to view)
- Very large collections may take several minutes to compile
- API rate limits may affect compilation of large collections

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for use with the Outline API. Please ensure your use complies with Outline's terms of service and API usage policies.

## Related Tools

- [Outline API Documentation](https://www.getoutline.com/developers)
- [Outline OpenAPI Spec](https://github.com/outline/openapi)

## Support

For issues related to:
- **This tool**: Open an issue in this repository
- **Outline API**: See [Outline's documentation](https://www.getoutline.com/developers)
- **Outline application**: Contact [Outline support](https://www.getoutline.com/contact)
