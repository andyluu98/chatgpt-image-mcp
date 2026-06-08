from cgimg.research.channels import _finding, CHANNELS


def test_finding_shape():
    f = _finding("youtube", "T", "u", engagement={"views": 5})
    assert f["platform"] == "youtube" and f["url"] == "u"
    assert set(f) == {"platform", "title", "url", "text", "author", "engagement", "published_at"}


def test_youtube_registered():
    assert "youtube" in CHANNELS
