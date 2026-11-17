import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_sources(path=None):
    """Return the source list. Each gets a `source` key (the slug) used in file names and posting_ids."""
    data = json.loads(Path(path or ROOT / "sources.json").read_text(encoding="utf-8"))
    out = []
    for s in data["sources"]:
        out.append({"source": s["slug"], "name": s["name"], "system": s["system"], "url": s["url"]})
    keys = [s["source"] for s in out]
    assert len(keys) == len(set(keys)), "duplicate source slug"
    return out
