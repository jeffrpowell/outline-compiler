# Quick Start Guide

Get started with Outline Compiler in 3 easy steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests markdown
```

## Step 2: Get Your Credentials

1. **Get API Key**:
   - Log into Outline
   - Go to Settings → API & Apps
   - Create a new API key
   - Copy the key (starts with `sk_`)

2. **Get Collection ID**:
   - Navigate to the collection you want to compile
   - Look at the URL: `https://app.getoutline.com/collection/YOUR_COLLECTION_ID`
   - Copy the Collection ID

## Step 3: Run the Compiler

### Option A: Direct Command

```bash
python3 outline_compiler.py \
  --api-key YOUR_API_KEY \
  --collection-id YOUR_COLLECTION_ID
```

### Option B: Using Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```bash
OUTLINE_API_KEY=your_actual_api_key
OUTLINE_COLLECTION_ID=your_collection_id
```

3. Run with the helper script:
```bash
./compile_with_env.sh
```

## Result

You'll get a file named `outline_compilation.html` that contains all your documents!

Open it in any browser:
```bash
# Linux
xdg-open outline_compilation.html

# macOS  
open outline_compilation.html

# Windows
start outline_compilation.html
```

## What Gets Compiled?

- ✅ All published documents in the collection
- ✅ Full markdown content (converted to HTML)
- ✅ Document hierarchy (nested documents)
- ✅ Table of contents
- ✅ Author and date information
- ✅ Images and links (as references)

## Need Help?

See the full [README.md](README.md) for:
- Detailed documentation
- Troubleshooting guide
- Advanced usage
- Security best practices

## Example Output Structure

```
My Documentation Collection
├── Introduction
│   └── Getting Started
│       └── Installation
├── User Guide
│   ├── Basic Features
│   └── Advanced Features
└── API Reference
    ├── Authentication
    └── Endpoints
```

All rendered as a beautiful, single HTML file with:
- Syntax-highlighted code blocks
- Formatted tables
- Clickable table of contents
- Print-friendly styling
