#!/usr/bin/env python3
"""
Outline Document Compiler
Compiles all documents from an Outline collection into a single HTML file.
Documents are traversed in depth-first order.
"""

import argparse
import sys
import requests
import re
import time
from typing import List, Dict, Optional
import markdown
from datetime import datetime


class OutlineCompiler:
    def __init__(self, api_url: str, api_key: str, debug: bool = False, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the Outline compiler.
        
        Args:
            api_url: Base URL for the Outline API (e.g., https://app.getoutline.com/api)
            api_key: API key for authentication
            debug: Enable debug output
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
            retry_delay: Initial delay in seconds between retries, uses exponential backoff (default: 1.0)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key.strip()  # Remove any whitespace
        self.debug = debug
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'tables',
            'fenced_code',
            'toc'
        ])
        # Mapping of document UUID to anchor ID in compiled HTML
        self.doc_uuid_to_anchor = {}
    
    def _make_request(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a POST request to the Outline API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., 'collections.info')
            data: Request payload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint}"
        
        if self.debug:
            print(f"DEBUG: Making request to {url}", file=sys.stderr)
            print(f"DEBUG: Headers: {dict((k, v[:20] + '...' if k == 'Authorization' else v) for k, v in self.headers.items())}", file=sys.stderr)
            print(f"DEBUG: Payload: {data}", file=sys.stderr)
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(url, headers=self.headers, json=data or {})
                
                if self.debug:
                    print(f"DEBUG: Response status: {response.status_code}", file=sys.stderr)
                    print(f"DEBUG: Response headers: {dict(response.headers)}", file=sys.stderr)
                
                # Handle specific HTTP errors with better messages
                if response.status_code == 401:
                    error_detail = ""
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('error', error_json.get('message', ''))
                    except:
                        pass
                    
                    raise Exception(
                        f"Authentication failed (HTTP 401).\n"
                        f"  API URL: {url}\n"
                        f"  Error: {error_detail}\n"
                        f"  \n"
                        f"  Possible causes:\n"
                        f"  1. Invalid API key\n"
                        f"  2. API key has been revoked\n"
                        f"  3. API key doesn't have required scopes (needs 'read' or 'collections:read' and 'documents:read')\n"
                        f"  4. Incorrect API URL (check if using self-hosted vs cloud)\n"
                        f"  \n"
                        f"  To verify your API key, run:\n"
                        f"    python3 outline_compiler.py --verify-auth --api-key YOUR_KEY"
                    )
                
                # Check for non-200 status codes and retry if needed
                if response.status_code != 200:
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Warning: Received HTTP {response.status_code} from {url}. Retrying in {delay:.1f}s... (attempt {attempt + 1}/{self.max_retries})", file=sys.stderr)
                        time.sleep(delay)
                        continue
                    else:
                        # Final attempt failed, raise the error
                        response.raise_for_status()
                
                response.raise_for_status()
                result = response.json()
                
                if not result.get('ok', True):
                    raise Exception(f"API error: {result.get('error', 'Unknown error')}")
                
                return result
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if "Authentication failed" in str(e):
                    raise
                
                # Retry on other request exceptions
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Warning: Request failed: {e}. Retrying in {delay:.1f}s... (attempt {attempt + 1}/{self.max_retries})", file=sys.stderr)
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    print(f"Error making request to {url}: {e}", file=sys.stderr)
                    raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise Exception(f"Failed to make request to {url} after {self.max_retries + 1} attempts")
    
    def get_collection_info(self, collection_id: str) -> Dict:
        """Get collection information."""
        result = self._make_request('collections.info', {'id': collection_id})
        return result.get('data', {})
    
    def get_collection_documents(self, collection_id: str) -> List[Dict]:
        """
        Get the document structure for a collection.
        
        Returns:
            List of NavigationNode objects representing the document tree
        """
        result = self._make_request('collections.documents', {'id': collection_id})
        return result.get('data', [])
    
    def get_document_info(self, document_id: str) -> Dict:
        """
        Get full information for a specific document.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            Document object with full content
        """
        result = self._make_request('documents.info', {'id': document_id})
        return result.get('data', {})
    
    def traverse_documents_dfs(self, nodes: List[Dict], depth: int = 0) -> List[tuple]:
        """
        Traverse document tree in depth-first order.
        
        Args:
            nodes: List of NavigationNode objects
            depth: Current depth in the tree (for indentation tracking)
            
        Returns:
            List of tuples (document_id, title, depth)
        """
        documents = []
        for node in nodes:
            doc_id = node.get('id')
            title = node.get('title', 'Untitled')
            documents.append((doc_id, title, depth))
            
            # Recursively process children
            children = node.get('children', [])
            if children:
                documents.extend(self.traverse_documents_dfs(children, depth + 1))
        
        return documents
    
    def _build_doc_uuid_mapping(self, documents: List[tuple]):
        """
        Build a mapping of document UUIDs to their anchor IDs in the compiled HTML.
        
        Args:
            documents: List of tuples (document_dict, depth)
        """
        self.doc_uuid_to_anchor = {}
        for i, (doc, _) in enumerate(documents):
            doc_id = doc.get('id')
            if doc_id:
                self.doc_uuid_to_anchor[doc_id] = f"doc-{i}"
    
    def _normalize_list_indentation(self, text: str) -> str:
        """
        Normalize list indentation from 2 spaces to 4 spaces.
        
        The Python markdown library requires 4 spaces for nested lists,
        but Outline uses 2 spaces. This function converts 2-space indentation
        to 4-space indentation for proper nested list rendering.
        
        Args:
            text: Markdown text with 2-space list indentation
            
        Returns:
            Markdown text with 4-space list indentation
        """
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Check if line starts with spaces followed by a list marker (* or -)
            if line and (line.lstrip().startswith('* ') or line.lstrip().startswith('- ')):
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                
                # If there are leading spaces (indicating nesting), double them
                if leading_spaces > 0:
                    # Double the indentation
                    new_indent = ' ' * (leading_spaces * 2)
                    normalized_lines.append(new_indent + line.lstrip())
                else:
                    # Top-level item, keep as is
                    normalized_lines.append(line)
            else:
                # Not a list item, keep as is
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def _extract_mermaid_blocks(self, text: str) -> tuple:
        """
        Extract mermaid code blocks and replace with placeholders.
        
        Args:
            text: Markdown text containing mermaid code blocks
            
        Returns:
            Tuple of (text_with_placeholders, list_of_mermaid_blocks)
        """
        # Pattern to match: ```mermaid or ```mermaidjs (with flexible whitespace)
        pattern = r'```mermaid(?:js)?\s*\n(.*?)\n```'
        
        mermaid_blocks = []
        
        def replace_with_placeholder(match):
            mermaid_code = match.group(1).strip()
            placeholder = f'MERMAID_PLACEHOLDER_{len(mermaid_blocks)}'
            mermaid_blocks.append(mermaid_code)
            return placeholder
        
        text_with_placeholders = re.sub(pattern, replace_with_placeholder, text, flags=re.DOTALL)
        return text_with_placeholders, mermaid_blocks
    
    def _restore_mermaid_blocks(self, html: str, mermaid_blocks: list) -> str:
        """
        Restore mermaid blocks from placeholders.
        
        Args:
            html: HTML with placeholders
            mermaid_blocks: List of mermaid code blocks
            
        Returns:
            HTML with mermaid divs restored
        """
        for i, mermaid_code in enumerate(mermaid_blocks):
            placeholder = f'MERMAID_PLACEHOLDER_{i}'
            mermaid_div = f'<div class="mermaid">\n{mermaid_code}\n</div>'
            
            # Replace placeholder, handling cases where it might be wrapped in <p> tags
            html = html.replace(f'<p>{placeholder}</p>', mermaid_div)
            html = html.replace(placeholder, mermaid_div)
        
        return html
    
    def _process_mention_links(self, html: str) -> str:
        """
        Convert Outline mention:// protocol links to internal document anchors.
        
        Outline uses: @<a href="mention://[UUID]/document/[UUID]">Document Name</a>
        We convert to: <a href="#doc-{i}">Document Name</a>
        
        Args:
            html: HTML content with mention:// links
            
        Returns:
            HTML with mention:// links converted to internal anchors
        """
        # Pattern to match: @<a href="mention://[UUID]/document/[UUID]">...</a>
        pattern = r'@<a href="mention://[^/]+/document/([^"]+)">([^<]+)</a>'
        
        def replace_mention(match):
            doc_uuid = match.group(1)
            doc_name = match.group(2)
            
            # Look up the anchor ID for this document UUID
            anchor_id = self.doc_uuid_to_anchor.get(doc_uuid)
            
            if anchor_id:
                return f'<a href="#{anchor_id}" class="mention-link" title="Jump to: {doc_name}">{doc_name}</a>'
            else:
                # If document not found in compilation, keep the name but make it non-clickable
                return f'<span class="mention-link-missing" title="Document not in compilation: {doc_name}">{doc_name}</span>'
        
        return re.sub(pattern, replace_mention, html)
    
    def compile_collection(self, collection_id: str, output_file: str):
        """
        Compile all documents from a collection into a single HTML file.
        
        Args:
            collection_id: UUID of the collection
            output_file: Path to output HTML file
        """
        print(f"Fetching collection information...")
        collection = self.get_collection_info(collection_id)
        collection_name = collection.get('name', 'Unknown Collection')
        collection_description = collection.get('description', '')
        
        print(f"Collection: {collection_name}")
        print(f"Fetching document structure...")
        
        doc_tree = self.get_collection_documents(collection_id)
        doc_list = self.traverse_documents_dfs(doc_tree)
        
        print(f"Found {len(doc_list)} documents")
        print(f"Fetching document content...")
        
        # Fetch all documents
        documents_with_content = []
        for i, (doc_id, title, depth) in enumerate(doc_list, 1):
            print(f"  [{i}/{len(doc_list)}] {title}")
            try:
                doc = self.get_document_info(doc_id)
                documents_with_content.append((doc, depth))
            except Exception as e:
                print(f"    Warning: Could not fetch document: {e}", file=sys.stderr)
        
        # Build document UUID to anchor mapping
        self._build_doc_uuid_mapping(documents_with_content)
        
        print(f"Generating HTML...")
        html = self._generate_html(collection_name, collection_description, documents_with_content)
        
        print(f"Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Done! Compiled {len(documents_with_content)} documents to {output_file}")
    
    def _generate_html(self, collection_name: str, collection_description: str, 
                      documents: List[tuple]) -> str:
        """
        Generate HTML from documents.
        
        Args:
            collection_name: Name of the collection
            collection_description: Description of the collection
            documents: List of tuples (document_dict, depth)
            
        Returns:
            Complete HTML document as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>{self._escape_html(collection_name)}</title>',
            '    <style>',
            '        body {',
            '            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '            line-height: 1.6;',
            '            max-width: 900px;',
            '            margin: 0 auto;',
            '            padding: 20px;',
            '            color: #333;',
            '        }',
            '        .header {',
            '            border-bottom: 3px solid #2684FF;',
            '            padding-bottom: 20px;',
            '            margin-bottom: 40px;',
            '        }',
            '        .header h1 {',
            '            margin: 0 0 10px 0;',
            '            color: #2684FF;',
            '        }',
            '        .header .meta {',
            '            color: #666;',
            '            font-size: 0.9em;',
            '        }',
            '        .collection-description {',
            '            background: #f5f5f5;',
            '            padding: 15px;',
            '            border-radius: 5px;',
            '            margin-bottom: 30px;',
            '        }',
            '        .document {',
            '            margin-bottom: 60px;',
            '            page-break-inside: avoid;',
            '        }',
            '        .document-header {',
            '            border-left: 4px solid #2684FF;',
            '            padding-left: 15px;',
            '            margin-bottom: 20px;',
            '        }',
            '        .document-title {',
            '            margin: 0 0 5px 0;',
            '            color: #2684FF;',
            '        }',
            '        .document-meta {',
            '            color: #666;',
            '            font-size: 0.85em;',
            '        }',
            '        .document-content {',
            '            padding-left: 20px;',
            '        }',
            '        .document-content ul {',
            '            margin: 10px 0;',
            '            padding-left: 30px;',
            '        }',
            '        .document-content ol {',
            '            margin: 10px 0;',
            '            padding-left: 30px;',
            '        }',
            '        .document-content li {',
            '            margin: 5px 0;',
            '        }',
            '        .depth-1 { margin-left: 20px; }',
            '        .depth-2 { margin-left: 40px; }',
            '        .depth-3 { margin-left: 60px; }',
            '        .depth-4 { margin-left: 80px; }',
            '        .depth-5 { margin-left: 100px; }',
            '        pre {',
            '            background: #f5f5f5;',
            '            padding: 15px;',
            '            border-radius: 5px;',
            '            overflow-x: auto;',
            '        }',
            '        code {',
            '            background: #f5f5f5;',
            '            padding: 2px 6px;',
            '            border-radius: 3px;',
            '            font-family: "Courier New", Courier, monospace;',
            '        }',
            '        pre code {',
            '            background: none;',
            '            padding: 0;',
            '        }',
            '        table {',
            '            border-collapse: collapse;',
            '            width: 100%;',
            '            margin: 20px 0;',
            '        }',
            '        th, td {',
            '            border: 1px solid #ddd;',
            '            padding: 12px;',
            '            text-align: left;',
            '        }',
            '        th {',
            '            background: #f5f5f5;',
            '            font-weight: bold;',
            '        }',
            '        blockquote {',
            '            border-left: 4px solid #ddd;',
            '            padding-left: 15px;',
            '            margin-left: 0;',
            '            color: #666;',
            '        }',
            '        img {',
            '            max-width: 100%;',
            '            height: auto;',
            '        }',
            '        a {',
            '            color: #2684FF;',
            '            text-decoration: none;',
            '        }',
            '        a:hover {',
            '            text-decoration: underline;',
            '        }',
            '        .toc {',
            '            background: #f9f9f9;',
            '            border: 1px solid #ddd;',
            '            padding: 20px;',
            '            margin-bottom: 40px;',
            '            border-radius: 5px;',
            '        }',
            '        .toc h2 {',
            '            margin-top: 0;',
            '        }',
            '        .toc > ul {',
            '            list-style-type: none;',
            '            padding-left: 0;',
            '        }',
            '        .toc ul ul {',
            '            padding-left: 30px;',
            '        }',
            '        .toc li {',
            '            margin: 5px 0;',
            '        }',
            '        .toc .depth-1 { margin-left: 20px; }',
            '        .toc .depth-2 { margin-left: 40px; }',
            '        .toc .depth-3 { margin-left: 60px; }',
            '        .toc .depth-4 { margin-left: 80px; }',
            '        .toc .depth-5 { margin-left: 100px; }',
            '        .mermaid {',
            '            background: #f9f9f9;',
            '            padding: 20px;',
            '            margin: 20px 0;',
            '            border-radius: 5px;',
            '            border: 1px solid #ddd;',
            '            text-align: center;',
            '        }',
            '        .mention-link {',
            '            color: #2684FF;',
            '            text-decoration: none;',
            '            font-weight: 500;',
            '            border-bottom: 1px dashed #2684FF;',
            '        }',
            '        .mention-link:hover {',
            '            text-decoration: none;',
            '            border-bottom: 1px solid #2684FF;',
            '        }',
            '        .mention-link-missing {',
            '            color: #999;',
            '            font-style: italic;',
            '            cursor: help;',
            '        }',
            '        @media print {',
            '            body { max-width: 100%; }',
            '            .document { page-break-after: always; }',
            '        }',
            '    </style>',
            '    <script type="module">',
            '        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";',
            '        mermaid.initialize({ startOnLoad: true, theme: "default" });',
            '    </script>',
            '</head>',
            '<body>',
            '    <div class="header">',
            f'        <h1>{self._escape_html(collection_name)}</h1>',
            f'        <div class="meta">Compiled on {timestamp}</div>',
            f'        <div class="meta">Derived from content located at <a href="https://outline.jeffpowell.dev">https://outline.jeffpowell.dev</a></div>',
            '    </div>',
        ]
        
        # Add collection description if present
        if collection_description:
            desc_html = self.md.convert(collection_description)
            html_parts.extend([
                '    <div class="collection-description">',
                '        <h3>Collection Description</h3>',
                f'        {desc_html}',
                '    </div>',
            ])
        
        # Add table of contents
        html_parts.append('    <div class="toc">')
        html_parts.append('        <h2>Table of Contents</h2>')
        html_parts.append('        <ul>')
        for i, (doc, depth) in enumerate(documents):
            title = doc.get('title', 'Untitled')
            depth_class = f'depth-{depth}' if depth > 0 else ''
            html_parts.append(f'            <li class="{depth_class}"><a href="#doc-{i}">{self._escape_html(title)}</a></li>')
        html_parts.append('        </ul>')
        html_parts.append('    </div>')
        
        # Add documents
        for i, (doc, depth) in enumerate(documents):
            title = doc.get('title', 'Untitled')
            text = doc.get('text', '')
            created_at = doc.get('createdAt', '')
            updated_at = doc.get('updatedAt', '')
            created_by = doc.get('createdBy', {})
            author_name = created_by.get('name', 'Unknown')
            
            # Normalize list indentation (2 spaces -> 4 spaces)
            if text:
                text = self._normalize_list_indentation(text)
            
            # Extract mermaid blocks before markdown conversion
            mermaid_blocks = []
            if text:
                text, mermaid_blocks = self._extract_mermaid_blocks(text)
            
            # Convert markdown to HTML
            self.md.reset()
            content_html = self.md.convert(text) if text else '<p><em>No content</em></p>'
            
            # Restore mermaid blocks after markdown conversion
            if mermaid_blocks:
                content_html = self._restore_mermaid_blocks(content_html, mermaid_blocks)
            
            # Process Outline mention links after markdown conversion
            content_html = self._process_mention_links(content_html)
            
            depth_class = f'depth-{depth}' if depth > 0 else ''
            
            html_parts.extend([
                f'    <div class="document {depth_class}" id="doc-{i}">',
                '        <div class="document-header">',
                f'            <h2 class="document-title">{self._escape_html(title)}</h2>',
                f'            <div class="document-meta">',
                f'                Last updated: {updated_at[:10] if updated_at else "Unknown"}',
                f'            </div>',
                '        </div>',
                '        <div class="document-content">',
                f'            {content_html}',
                '        </div>',
                '    </div>',
            ])
        
        html_parts.extend([
            '</body>',
            '</html>',
        ])
        
        return '\n'.join(html_parts)
    
    def verify_auth(self) -> bool:
        """
        Verify that the API key is valid and has correct permissions.
        
        Returns:
            True if authentication is successful
        """
        try:
            print("Verifying API authentication...")
            result = self._make_request('auth.info')
            
            if result.get('data'):
                user = result['data'].get('user', {})
                team = result['data'].get('team', {})
                
                print("✓ Authentication successful!")
                print(f"  User: {user.get('name', 'Unknown')} ({user.get('email', 'N/A')})")
                print(f"  Team: {team.get('name', 'Unknown')}")
                print(f"  User ID: {user.get('id', 'N/A')}")
                return True
            else:
                print("✗ Authentication failed: No data returned")
                return False
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


def main():
    parser = argparse.ArgumentParser(
        description='Compile Outline collection documents into a single HTML file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify your API key works
  %(prog)s --verify-auth --api-key YOUR_API_KEY
  
  # Using cloud-hosted Outline
  %(prog)s --api-key YOUR_API_KEY --collection-id COLLECTION_UUID
  
  # Using self-hosted Outline
  %(prog)s --api-url https://outline.example.com/api \\
           --api-key YOUR_API_KEY \\
           --collection-id COLLECTION_UUID \\
           --output mycompilation.html
  
  # Enable debug output
  %(prog)s --api-key YOUR_API_KEY --collection-id COLLECTION_UUID --debug
        """
    )
    
    parser.add_argument(
        '--api-url',
        default='https://app.getoutline.com/api',
        help='Outline API base URL (default: https://app.getoutline.com/api)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Outline API key (get from Settings => API & Apps)'
    )
    
    parser.add_argument(
        '--collection-id',
        help='UUID of the collection to compile'
    )
    
    parser.add_argument(
        '--output',
        default='outline_compilation.html',
        help='Output HTML file path (default: outline_compilation.html)'
    )
    
    parser.add_argument(
        '--verify-auth',
        action='store_true',
        help='Verify API key authentication and exit'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.api_key:
        parser.error('--api-key is required')
    
    if not args.verify_auth and not args.collection_id:
        parser.error('--collection-id is required (unless using --verify-auth)')
    
    try:
        compiler = OutlineCompiler(args.api_url, args.api_key, debug=args.debug)
        
        if args.verify_auth:
            success = compiler.verify_auth()
            sys.exit(0 if success else 1)
        
        compiler.compile_collection(args.collection_id, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
