"""Convert docs/LSB_System_Requirements_v2.0.docx to a markdown sidecar.

graphify does not ingest .docx; the sidecar puts the spec into the
knowledge-graph corpus. The .docx remains the canonical immutable spec.
Re-run after any (human-approved) spec change: python scripts/convert_spec_docx.py
"""
import html
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "LSB_System_Requirements_v2.0.docx"
DST = ROOT / "docs" / "LSB_System_Requirements_v2.0.md"

with zipfile.ZipFile(SRC) as z:
    xml = z.read("word/document.xml").decode("utf-8")

out = []
for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
    style = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S)
    line = html.unescape("".join(texts)).strip()
    if not line:
        continue
    s = style.group(1) if style else ""
    if s.startswith("Heading"):
        lvl = int(re.sub(r"\D", "", s) or 1)
        out.append("#" * min(lvl, 6) + " " + line)
    elif s == "ListParagraph":
        out.append("- " + line)
    else:
        out.append(line)

md = (
    "> Auto-converted from LSB_System_Requirements_v2.0.docx for the graphify "
    "corpus. The .docx remains the canonical immutable spec.\n\n"
    + "\n\n".join(out)
    + "\n"
)
DST.write_text(md, encoding="utf-8")
print(f"paragraphs: {len(out)} | chars: {len(md)}")
print(md[:500])
