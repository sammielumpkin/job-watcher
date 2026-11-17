import gzip
import json

from jobwatcher.fetch import fetch_all

GOOD = json.dumps({"jobs": [{"id": 1, "title": "A"}]}).encode()
SRC = lambda k, system="greenhouse": {"source": k, "name": k.title(), "system": system, "url": "http://x/" + k}


def fake_get(url):
    if url.endswith("/bad"):
        raise OSError("blocked")
    if url.endswith("/html"):
        return b"<html>nope</html>"
    if url.endswith("/empty"):
        return b'{"jobs": []}'
    return GOOD


def test_failed_sources_do_not_stop_run_and_write_no_file(tmp_path):
    srcs = [SRC("good"), SRC("bad"), SRC("html"), SRC("empty")]
    res = fetch_all(srcs, tmp_path, "2026-11-16", get=fake_get, pause=0)
    assert {r["source"]: r["ok"] for r in res} == {"good": True, "bad": False, "html": False, "empty": False}
    assert [r["count"] for r in res] == [1, 0, 0, 0]
    assert all(r["error"] for r in res if not r["ok"])
    files = sorted(p.name for p in (tmp_path / "2026-11-16").iterdir())
    assert files == ["good.json.gz"]
    assert json.loads(gzip.decompress((tmp_path / "2026-11-16/good.json.gz").read_bytes())) == json.loads(GOOD)


def test_rerun_same_day_replaces_files(tmp_path):
    fetch_all([SRC("good"), SRC("other")], tmp_path, "2026-11-16", get=fake_get, pause=0)
    fetch_all([SRC("good"), SRC("bad")], tmp_path, "2026-11-16", get=fake_get, pause=0)
    assert [p.name for p in (tmp_path / "2026-11-16").iterdir()] == ["good.json.gz"]
