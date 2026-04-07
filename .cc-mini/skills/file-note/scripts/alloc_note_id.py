#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NOTE_RE = re.compile(r"^(\d+)_")


def next_note_id(notes_dir: Path) -> int:
    max_id = 0
    if notes_dir.exists():
        for p in notes_dir.iterdir():
            if not p.is_file():
                continue
            m = NOTE_RE.match(p.name)
            if m:
                max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Allocate the next file-note numeric id")
    parser.add_argument("--notes-dir", default="./code-reading-notes/10_file_notes", help="Directory containing file note markdown files")
    parser.add_argument("--width", type=int, default=3, help="Zero-pad width, default 3")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    notes_dir = Path(args.notes_dir).expanduser().resolve()
    notes_dir.mkdir(parents=True, exist_ok=True)

    num = next_note_id(notes_dir)
    padded = str(num).zfill(args.width)

    result = {
        "notes_dir": str(notes_dir),
        "next_id": num,
        "next_id_padded": padded,
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(padded)


if __name__ == "__main__":
    main()
