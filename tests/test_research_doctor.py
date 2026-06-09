from cgimg.research import doctor


def test_doctor_returns_dict_with_known_channels():
    rep = doctor.check_channels()
    assert isinstance(rep, dict) and len(rep) >= 1
    # youtube should be reported (ok, since yt-dlp is installed)
    assert "youtube" in rep
    assert all(v in ("ok", "missing") for v in rep.values())
