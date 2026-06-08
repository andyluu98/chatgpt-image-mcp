import cgimg.research._arpath  # noqa: F401  (side effect: makes `agent_reach` importable)


def test_agent_reach_base_imports():
    import importlib
    m = importlib.import_module("agent_reach.channels.base")
    assert hasattr(m, "Channel")


def test_agent_reach_web_channel_imports():
    import importlib
    m = importlib.import_module("agent_reach.channels.web")
    assert hasattr(m, "WebChannel")
    assert hasattr(m.WebChannel, "read")


def test_agent_reach_doctor_imports():
    import importlib
    m = importlib.import_module("agent_reach.doctor")
    assert hasattr(m, "check_all")
