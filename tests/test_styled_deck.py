"""Offline wiring checks for the styled_deck feature (no network)."""


def test_generate_image_accepts_ref_image_param():
    import inspect
    from cgimg.engine import generate
    sig = inspect.signature(generate.generate_image)
    assert "ref_image" in sig.parameters


def test_styled_deck_exists():
    from cgimg.branding import deck
    assert hasattr(deck, "styled_deck")


def test_generate_image_accepts_ref_mode_param():
    import inspect
    from cgimg.engine import generate
    sig = inspect.signature(generate.generate_image)
    assert "ref_mode" in sig.parameters
    assert sig.parameters["ref_mode"].default == "style"


def test_ref_suffix_logo_mode_says_keep_logo_exact():
    from cgimg.engine.generate import _ref_suffix
    logo = _ref_suffix("logo")
    assert "LOGO" in logo and "CHÍNH XÁC" in logo
    assert _ref_suffix("asset") == logo  # alias


def test_ref_suffix_style_mode_says_do_not_copy():
    from cgimg.engine.generate import _ref_suffix
    style = _ref_suffix("style")
    assert "PHONG CÁCH" in style and "KHÔNG sao chép" in style
    # the two modes must give different instructions
    assert style != _ref_suffix("logo")
