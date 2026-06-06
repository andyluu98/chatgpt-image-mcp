from cgimg.engine import enhance


def test_long_prompt_skipped():
    long = "x " * 200  # > 280 chars
    assert enhance.enhance_prompt(long).strip() == long.strip()


def test_template_fallback_is_rich(monkeypatch):
    # Force the LLM path to fail -> must fall back to template, never raise.
    import cgimg.auth.tokens as t
    monkeypatch.setattr(t, "get_access_token", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    out = enhance.enhance_prompt("ai agent")
    assert "ai agent" in out.lower()
    assert len(out) > len("ai agent")  # got enriched
