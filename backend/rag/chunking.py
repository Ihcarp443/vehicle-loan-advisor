"""Split one vehicle brochure (VH001.md ...) into section-level chunks with metadata."""
import re
from pathlib import Path

KNOWN_HEADINGS = {"Overview", "Design and Comfort", "Safety", "Powertrain and Efficiency",
                  "Technology and Features", "Ownership", "Who It Suits"}
MAX_CHARS = 1000


def _split_long(body):
    """Long sections (e.g. the trim-by-trim feature list) are split by line so chunks stay focused."""
    if len(body) <= MAX_CHARS:
        return [body]
    parts, current = [], ""
    for line in body.splitlines():
        if current and len(current) + len(line) > MAX_CHARS:
            parts.append(current.strip())
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.strip())
    return parts


def chunk_brochure(path):
    path = Path(path)
    vehicle_id = path.stem.split("_")[0]
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((l.lstrip("# ").strip() for l in lines if l.strip()), vehicle_id)
    vehicle_name = title.split(":")[0].replace("Brochure", "").strip()

    sections, name, buf = [], "Introduction", []
    for line in lines[1:]:
        s = line.strip()
        m = re.match(r"^#{2,3}\s+(.*)", s)
        heading = m.group(1).strip() if m else (s if s in KNOWN_HEADINGS else None)
        if heading:
            sections.append((name, "\n".join(buf).strip()))
            name, buf = heading, []
        else:
            buf.append(line)
    sections.append((name, "\n".join(buf).strip()))

    chunks = []
    for section, body in sections:
        if not body or body.upper().startswith("SYNTHETIC"):
            continue
        for part in _split_long(body):
            chunks.append({
                "chunk_id": f"{vehicle_id}-{len(chunks)}",
                "vehicle_id": vehicle_id,
                "vehicle_name": vehicle_name,
                "section": section,
                "file": path.name,
                "text": part,
                # the text that gets embedded carries the vehicle and section name for better matching
                "embed_text": f"{vehicle_name} - {section}\n{part}",
            })
    return chunks
