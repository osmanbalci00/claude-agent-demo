#!/usr/bin/env python3
"""Folder-organizing agent.

Sorts the files in a folder into subfolders by type, renames duplicates
instead of overwriting, and writes a Markdown report whose summary is
written by a local Ollama model (qwen2.5:3b). Standard library only.

Usage:
    python3 organize_agent.py messy
    python3 organize_agent.py messy --dry-run
    python3 organize_agent.py messy --no-llm
"""

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"
REPORT_NAME = "organize_report.md"

CATEGORIES = {
    "documents": {".txt", ".md", ".pdf", ".doc", ".docx", ".rtf", ".odt", ".pages", ".tex", ".epub"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".tif", ".heic", ".ico"},
    "spreadsheets": {".csv", ".tsv", ".xls", ".xlsx", ".ods", ".numbers"},
    "code": {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".c", ".h", ".cpp",
             ".go", ".rs", ".rb", ".php", ".sh", ".json", ".yaml", ".yml", ".toml", ".sql", ".ipynb"},
}
OTHER = "other"
CATEGORY_DIRS = set(CATEGORIES) | {OTHER}


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    for category, exts in CATEGORIES.items():
        if ext in exts:
            return category
    return OTHER


def safe_destination(dest_dir: Path, name: str, reserved: set) -> Path:
    """Return a path in dest_dir that doesn't exist yet: 'name (1).ext', 'name (2).ext', ..."""
    candidate = dest_dir / name
    stem, suffix = Path(name).stem, Path(name).suffix
    n = 1
    while candidate.exists() or candidate in reserved:
        candidate = dest_dir / f"{stem} ({n}){suffix}"
        n += 1
    return candidate


def organize(folder: Path, dry_run: bool):
    moved, skipped = [], []
    reserved = set()  # destinations claimed during this run (matters for dry runs)

    for item in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if item.name == REPORT_NAME:
            continue
        if item.is_symlink():
            skipped.append((item.name, "symlink (left alone for safety)"))
        elif item.is_dir():
            reason = "category folder" if item.name in CATEGORY_DIRS else "subfolder (not touched)"
            skipped.append((item.name + "/", reason))
        elif item.name.startswith("."):
            skipped.append((item.name, "hidden file"))
        elif not item.is_file():
            skipped.append((item.name, "not a regular file"))
        else:
            category = classify(item)
            dest_dir = folder / category
            dest = safe_destination(dest_dir, item.name, reserved)
            reserved.add(dest)
            try:
                if not dry_run:
                    dest_dir.mkdir(exist_ok=True)
                    # Re-check right before moving so nothing is ever overwritten.
                    if dest.exists():
                        dest = safe_destination(dest_dir, item.name, reserved)
                    shutil.move(str(item), str(dest))
                moved.append({
                    "file": item.name,
                    "category": category,
                    "new_name": dest.name,
                    "renamed": dest.name != item.name,
                })
            except OSError as e:
                skipped.append((item.name, f"move failed: {e}"))
    return moved, skipped


def ask_ollama(moved, skipped, dry_run: bool):
    counts = {}
    for m in moved:
        counts[m["category"]] = counts.get(m["category"], 0) + 1
    renamed = sum(m["renamed"] for m in moved)
    # Small models count badly, so hand over totals already computed.
    facts = {
        "mode": "dry run (nothing actually moved)" if dry_run else "files were moved",
        "total_files_moved": len(moved),
        "total_files_renamed": renamed,
        "total_items_skipped": len(skipped),
        "files_moved_per_category": counts,
        "renamed_to_avoid_overwrite": [f'{m["file"]} -> {m["category"]}/{m["new_name"]}'
                                       for m in moved if m["renamed"]],
        "skipped": [f"{n} ({r})" for n, r in skipped],
    }
    prompt = (
        "You are a file-organizing assistant. Write a short, friendly summary (2-4 sentences, "
        "plain text, no lists, no headings) of this folder cleanup. Use ONLY these facts and "
        "copy the totals exactly as given; do not count, guess, or invent files or numbers.\n\n"
        + json.dumps(facts, indent=2)
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["message"]["content"].strip()


def fallback_summary(moved, skipped, dry_run: bool):
    verb = "Would move" if dry_run else "Moved"
    renamed = sum(m["renamed"] for m in moved)
    return (f"{verb} {len(moved)} file(s), renamed {renamed} to avoid overwriting, "
            f"and skipped {len(skipped)} item(s). (Ollama was unavailable; summary written without the model.)")


def write_report(folder: Path, moved, skipped, summary: str, dry_run: bool) -> Path:
    lines = [
        "# Folder Organization Report",
        "",
        f"- Folder: `{folder}`",
        f"- Date: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Mode: {'DRY RUN — nothing was moved' if dry_run else 'live'}",
        "",
        "## Summary",
        "",
        summary,
        "",
        f"## {'Would move' if dry_run else 'Moved'} ({len(moved)})",
        "",
    ]
    if moved:
        lines += ["| File | Destination | Note |", "|---|---|---|"]
        for m in moved:
            note = "renamed (name already taken)" if m["renamed"] else ""
            lines.append(f'| {m["file"]} | {m["category"]}/{m["new_name"]} | {note} |')
    else:
        lines.append("Nothing to move.")
    lines += ["", f"## Skipped ({len(skipped)})", ""]
    lines += [f"- `{name}` — {reason}" for name, reason in skipped] or ["Nothing skipped."]
    report = folder / REPORT_NAME
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Sort a messy folder into subfolders by file type.")
    parser.add_argument("folder", help="folder to organize")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without moving anything")
    parser.add_argument("--no-llm", action="store_true", help="don't call Ollama for the summary")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f"Not a folder: {folder}")

    moved, skipped = organize(folder, args.dry_run)

    summary = None
    if not args.no_llm:
        try:
            print(f"Asking {MODEL} for a summary...")
            summary = ask_ollama(moved, skipped, args.dry_run)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            print(f"Ollama unavailable ({e}); using a plain summary.")
    summary = summary or fallback_summary(moved, skipped, args.dry_run)

    report = write_report(folder, moved, skipped, summary, args.dry_run)
    for m in moved:
        tag = "  (renamed)" if m["renamed"] else ""
        print(f'  {m["file"]:<24} -> {m["category"]}/{m["new_name"]}{tag}')
    for name, reason in skipped:
        print(f"  skipped {name}: {reason}")
    print(f"\nReport written to {report}")


if __name__ == "__main__":
    main()
