"""Offline wiring checks for the styled_deck feature (no network)."""


def test_generate_image_accepts_ref_image_param():
    import inspect
    from cgimg.engine import generate
    sig = inspect.signature(generate.generate_image)
    assert "ref_image" in sig.parameters


def test_styled_deck_exists():
    from cgimg.branding import deck
    assert hasattr(deck, "styled_deck")
