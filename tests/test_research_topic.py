from cgimg.research import channels


def test_research_topic_aggregates(monkeypatch, tmp_path):
    monkeypatch.setitem(channels.CHANNELS, "youtube",
                        lambda q, limit=10: [channels._finding("youtube", "T1", "u1",
                                             engagement={"views": 100})])
    monkeypatch.setitem(channels.CHANNELS, "x",
                        lambda q, limit=10: [channels._finding("x", "T2", "u2")])
    res = channels.research_topic("x", platforms=["youtube", "x"],
                                  out_path=str(tmp_path / "b.md"))
    assert len(res["insights"]) == 2
    assert res["by_platform"].get("youtube") == 1


def test_research_topic_skips_broken_channel(monkeypatch, tmp_path):
    def boom(q, limit=10):
        raise RuntimeError("cli missing")
    monkeypatch.setitem(channels.CHANNELS, "youtube", boom)
    monkeypatch.setitem(channels.CHANNELS, "x",
                        lambda q, limit=10: [channels._finding("x", "T", "u")])
    res = channels.research_topic("x", platforms=["youtube", "x"],
                                  out_path=str(tmp_path / "b.md"))
    assert len(res["insights"]) == 1


def test_twitter_graceful_without_cli(monkeypatch):
    import shutil
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    assert channels.twitter("anything") == []
