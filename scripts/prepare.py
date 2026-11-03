"""Prepare plain Markdown for Jekyll without changing the source articles."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".build-source"
# Copy into a dedicated build directory; never modify docs/ originals.
OUTPUT.mkdir(exist_ok=True)
for entry in ROOT.iterdir():
    if entry.name in {".git", ".github", ".build-source", ".image-repo", "scripts", "publish.cmd", "publish.ps1", "README.md"}:
        continue
    target = OUTPUT / entry.name
    if entry.is_dir():
        shutil.copytree(entry, target, dirs_exist_ok=True)
    else:
        shutil.copy2(entry, target)

count = 0
for path in (OUTPUT / "docs").rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".md", ".markdown"}:
        continue
    body = path.read_text(encoding="utf-8-sig")
    if re.match(r"^---\s*\n", body):
        count += 1
        continue
    heading = re.search(r"^# +(.+?)\s*#*\s*$", body, re.MULTILINE)
    title = heading.group(1).strip() if heading else path.stem
    metadata = "---\ntitle: " + json.dumps(title, ensure_ascii=False)
    metadata += "\nhas_heading: " + ("true" if heading else "false") + "\n---\n\n"
    path.write_text(metadata + body, encoding="utf-8")
    count += 1
print(f"Prepared {count} article(s) in .build-source; originals unchanged.")
