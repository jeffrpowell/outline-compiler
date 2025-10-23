#!/usr/bin/env python3
"""
Outline Document Compiler
Compiles all documents from an Outline collection into a single HTML file.
Documents are traversed in depth-first order.
"""

import argparse
import sys
import requests
from typing import List, Dict, Optional
import markdown
from datetime import datetime


class OutlineCompiler:
    def __init__(self, api_url: str, api_key: str):
        """
        Initialize the Outline compiler.
        
        Args:
            api_url: Base URL for the Outline API (e.g., https://app.getoutline.com/api)
            api_key: API key for authentication
        """
        self.api_url = api_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
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
    
    def _make_request(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a POST request to the Outline API.
        
        Args:
            endpoint: API endpoint (e.g., 'collections.info')
            data: Request payload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=data or {})
            response.raise_for_status()
            result = response.json()
            
            if not result.get('ok', True):
                raise Exception(f"API error: {result.get('error', 'Unknown error')}")
            
            return result
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}", file=sys.stderr)
            raise
    
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
            '        .depth-1 { padding-left: 20px; }',
            '        .depth-2 { padding-left: 40px; }',
            '        .depth-3 { padding-left: 60px; }',
            '        .depth-4 { padding-left: 80px; }',
            '        .depth-5 { padding-left: 100px; }',
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
            '        .toc ul {',
            '            list-style-type: none;',
            '            padding-left: 0;',
            '        }',
            '        .toc li {',
            '            margin: 5px 0;',
            '        }',
            '        .toc .depth-1 { padding-left: 20px; }',
            '        .toc .depth-2 { padding-left: 40px; }',
            '        .toc .depth-3 { padding-left: 60px; }',
            '        @media print {',
            '            body { max-width: 100%; }',
            '            .document { page-break-after: always; }',
            '        }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="header">',
            f'        <h1>{self._escape_html(collection_name)}</h1>',
            f'        <div class="meta">Compiled on {timestamp}</div>',
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
            
            # Convert markdown to HTML
            self.md.reset()
            content_html = self.md.convert(text) if text else '<p><em>No content</em></p>'
            
            depth_class = f'depth-{depth}' if depth > 0 else ''
            
            html_parts.extend([
                f'    <div class="document {depth_class}" id="doc-{i}">',
                '        <div class="document-header">',
                f'            <h2 class="document-title">{self._escape_html(title)}</h2>',
                f'            <div class="document-meta">',
                f'                Author: {self._escape_html(author_name)} | ',
                f'                Updated: {updated_at[:10] if updated_at else "Unknown"}',
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
  # Using cloud-hosted Outline
  %(prog)s --api-key YOUR_API_KEY --collection-id COLLECTION_UUID
  
  # Using self-hosted Outline
  %(prog)s --api-url https://outline.example.com/api \\
           --api-key YOUR_API_KEY \\
           --collection-id COLLECTION_UUID \\
           --output mycompilation.html
        """
    )
    
    parser.add_argument(
        '--api-url',
        default='https://app.getoutline.com/api',
        help='Outline API base URL (default: https://app.getoutline.com/api)'
    )
    
    parser.add_argument(
        '--api-key',
        required=True,
        help='Outline API key (get from Settings => API & Apps)'
    )
    
    parser.add_argument(
        '--collection-id',
        required=True,
        help='UUID of the collection to compile'
    )
    
    parser.add_argument(
        '--output',
        default='outline_compilation.html',
        help='Output HTML file path (default: outline_compilation.html)'
    )
    
    args = parser.parse_args()
    
    try:
        compiler = OutlineCompiler(args.api_url, args.api_key)
        compiler.compile_collection(args.collection_id, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
