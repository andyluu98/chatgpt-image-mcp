from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
from cgimg.ppt.builder import build_pptx


def _sample_png(p: Path, w=1672, h=941):
    Image.new("RGB", (w, h), (26, 58, 140)).save(p)


def test_build_169_deck(tmp_path):
    imgs = []
    for i in range(2):
        ip = tmp_path / f"s{i}.png"
        _sample_png(ip)
        imgs.append(str(ip))
    out = tmp_path / "deck.pptx"
    result = build_pptx(imgs, str(out), aspect="16:9")
    assert Path(result).exists()
    prs = Presentation(result)
    assert len(prs.slides) == 2
    assert round(prs.slide_width / Inches(1), 2) == 13.33
    assert round(prs.slide_height / Inches(1), 2) == 7.5


def test_empty_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        build_pptx([], str(tmp_path / "x.pptx"))


def test_missing_image_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        build_pptx([str(tmp_path / "nope.png")], str(tmp_path / "x.pptx"))


def test_unknown_aspect_raises(tmp_path):
    import pytest
    ip = tmp_path / "s.png"
    _sample_png(ip)
    with pytest.raises(ValueError):
        build_pptx([str(ip)], str(tmp_path / "x.pptx"), aspect="banana")
