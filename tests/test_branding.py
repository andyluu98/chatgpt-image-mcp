from pathlib import Path
from PIL import Image
import pytest
from cgimg.branding.colors import extract_brand_colors
from cgimg.branding.composite import overlay_logo


def test_extract_colors_finds_dominant(tmp_path):
    # Logo: mostly navy with a gold block, on transparent bg.
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for x in range(100):
        for y in range(100):
            if x < 70:
                img.putpixel((x, y), (26, 58, 140, 255))   # navy
            else:
                img.putpixel((x, y), (201, 160, 76, 255))  # gold
    p = tmp_path / "logo.png"; img.save(p)
    colors = extract_brand_colors(str(p), max_colors=2)
    assert len(colors) >= 1
    assert all(c.startswith("#") and len(c) == 7 for c in colors)
    # navy should be the most prominent (70% of opaque pixels)
    # allow quantization: just assert a blue-ish dominant color is first
    r, g, b = int(colors[0][1:3],16), int(colors[0][3:5],16), int(colors[0][5:7],16)
    assert b > r and b > g  # blue dominant


def test_extract_ignores_transparent(tmp_path):
    img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))  # fully transparent
    for x in range(50):
        for y in range(25):
            img.putpixel((x, y), (10, 200, 50, 255))  # green top half
    p = tmp_path / "logo.png"; img.save(p)
    colors = extract_brand_colors(str(p))
    r, g, b = int(colors[0][1:3],16), int(colors[0][3:5],16), int(colors[0][5:7],16)
    assert g > r and g > b  # green dominant, transparent ignored


def test_overlay_logo_keeps_base_size(tmp_path):
    base = Image.new("RGB", (1672, 941), (20, 20, 30)); bp = tmp_path / "base.png"; base.save(bp)
    logo = Image.new("RGBA", (200, 80), (255, 0, 0, 255)); lp = tmp_path / "logo.png"; logo.save(lp)
    out = tmp_path / "out.png"
    res = overlay_logo(str(bp), str(lp), str(out), position="top-left", scale=0.15)
    assert Path(res).exists()
    im = Image.open(res)
    assert im.size == (1672, 941)  # base size unchanged


def test_overlay_bad_position(tmp_path):
    base = Image.new("RGB", (100, 100), (0,0,0)); bp = tmp_path / "b.png"; base.save(bp)
    logo = Image.new("RGBA", (10, 10), (255,0,0,255)); lp = tmp_path / "l.png"; logo.save(lp)
    with pytest.raises(ValueError):
        overlay_logo(str(bp), str(lp), str(tmp_path/"o.png"), position="middle")
