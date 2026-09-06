#!/usr/bin/env python3
"""Compile every configured Outline collection into HTML.

Reads:
  .env              KEY=VALUE lines:
                        OUTLINE_API_KEY      (required)
                        OUTLINE_API_URL      (default: cloud Outline)
                        OUTLINE_EXPORT_DIR   (base folder for output, default ~/outline-exports)
  collections.txt   one collection per line:   <slug>  <collection-id>
                    (separate slug and id with spaces/tabs; '#' comments and
                     blank lines are ignored. slug becomes the output folder name)

Writes (per collection):
  $OUTLINE_EXPORT_DIR/<slug>/index.html   +   attachments/

Usage:
  run_all.py               run every collection in collections.txt
  run_all.py --slug NAME   run only the collection with that slug
  run_all.py --check       validate config and print the plan (no network)

Exit status: 0 if every requested collection compiled, 1 otherwise.
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
ENV_FILE = REPO / ".env"
COLLECTIONS_FILE = REPO / "collections.txt"
COMPILER = REPO / "outline_compiler.py"
DEFAULT_EXPORT_DIR = Path.home() / "outline-exports"
DEFAULT_API_URL = "https://app.getoutline.com/api"
PLACEHOLDER_KEY = "your_api_key_here"


def load_env(path: Path) -> dict:
    """Parse a simple KEY=VALUE env file (no shell needed)."""
    vals = {}
    if not path.is_file():
        return vals
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        vals[key.strip()] = val
    return vals


def parse_collections(path: Path):
    """Return a list of (slug, collection_id); None if the file is missing."""
    if not path.is_file():
        return None
    cols = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            print(f"  ! skipping (need 'slug  collection-id'): {line!r}",
                  file=sys.stderr)
            continue
        cols.append((parts[0], parts[1]))
    return cols


def build_command(api_url, api_key, collection_id, out_dir):
    return [
        sys.executable, str(COMPILER),
        "--api-url", api_url,
        "--api-key", api_key,
        "--collection-id", collection_id,
        "--output", str(out_dir),
    ]


def redacted(cmd):
    """Return cmd with the value following --api-key masked for logging."""
    out, hide_next = [], False
    for tok in cmd:
        if hide_next:
            out.append("[hidden]")
            hide_next = False
            continue
        if tok == "--api-key":
            hide_next = True
        out.append(tok)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", help="only run this collection slug")
    ap.add_argument("--check", action="store_true",
                    help="validate config and print the plan without running")
    args = ap.parse_args()

    env = load_env(ENV_FILE)
    api_key = env.get("OUTLINE_API_KEY", "").strip()
    api_url = (env.get("OUTLINE_API_URL") or DEFAULT_API_URL).strip() or DEFAULT_API_URL
    export_dir = Path((env.get("OUTLINE_EXPORT_DIR") or str(DEFAULT_EXPORT_DIR)).strip())
    export_dir = export_dir.expanduser()
    if not export_dir.is_absolute():
        export_dir = REPO / export_dir

    key_ok = bool(api_key) and api_key != PLACEHOLDER_KEY
    cols = parse_collections(COLLECTIONS_FILE)

    problems = []
    if not COMPILER.is_file():
        problems.append(f"compiler not found: {COMPILER}")
    if cols is None:
        problems.append(f"collections file not found: {COLLECTIONS_FILE}")
    elif not cols:
        problems.append(f"no collections listed in {COLLECTIONS_FILE}")
    if not key_ok:
        problems.append("OUTLINE_API_KEY is missing or still the placeholder in .env")
    if args.slug and cols is not None:
        cols = [c for c in cols if c[0] == args.slug]
        if not cols:
            problems.append(f"no collection named {args.slug!r} in collections.txt")

    if args.check:
        print("Config check")
        print(f"  compiler        : {COMPILER}")
        print(f"  api-url         : {api_url}")
        print(f"  api-key         : {'set' if key_ok else 'MISSING / placeholder'}")
        print(f"  export dir      : {export_dir}")
        print(f"  collections.txt : {COLLECTIONS_FILE}")
        if cols is not None:
            print(f"  collections     : {len(cols)}")
            for slug, cid in cols:
                print(f"    - {slug}  ->  {cid}")
        if problems:
            print("\nProblems:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("\nOK: configuration looks complete "
              "(--check does not contact the Outline API).")
        return 0

    # Real run.
    if problems:
        for p in problems:
            print(f"Error: {p}", file=sys.stderr)
        return 1

    # If we reach here, `problems` is empty, so a collections list exists.
    assert cols is not None

    export_dir.mkdir(parents=True, exist_ok=True)
    ok, failed = [], []
    for slug, cid in cols:
        out_dir = export_dir / slug
        cmd = build_command(api_url, api_key, cid, out_dir)
        print(f"\n=== {slug} ({cid}) -> {out_dir} ===", flush=True)
        print("  " + " ".join(redacted(cmd)))
        proc = subprocess.run(cmd)
        if proc.returncode == 0:
            ok.append(slug)
        else:
            failed.append(slug)

    print("\n=== Summary ===")
    print(f"  succeeded: {len(ok)}/{len(cols)}")
    if failed:
        print(f"  failed   : {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
