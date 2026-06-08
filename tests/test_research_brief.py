from pathlib import Path
from cgimg.research.brief import build_brief


def _f(platform, title, url, views):
    return {"platform": platform, "title": title, "url": url, "text": "",
            "author": "", "engagement": {"views": views}, "published_at": None}


def test_build_brief_structure(tmp_path):
    findings = [
        _f("youtube", "VN-Index tăng mạnh", "u1", 9000),
        _f("web", "VN-Index tăng mạnh hôm nay", "u2", 100),
        _f("youtube", "Giá vàng lập đỉnh", "u3", 500),
    ]
    out = tmp_path / "brief.md"
    res = build_brief("chứng khoán", findings, str(out))
    assert Path(res["brief_path"]).exists()
    md = out.read_text(encoding="utf-8")
    assert "chứng khoán" in md
    assert "VN-Index" in md
    assert len(res["insights"]) == 2          # VN-Index items merge
    assert "youtube" in res["by_platform"]


def test_build_brief_empty(tmp_path):
    res = build_brief("topic", [], str(tmp_path / "b.md"))
    assert res["insights"] == []
    assert Path(res["brief_path"]).exists()
