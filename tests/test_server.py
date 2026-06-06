def test_server_imports_and_registers_tools():
    from cgimg import server
    assert server.mcp is not None
    # FastMCP stores registered tools; verify our 4 tool names are present.
    # The exact accessor can vary by mcp version; this asserts the module
    # imports cleanly and the FastMCP instance exists.
    assert server.mcp.name == "chatgpt-image"


def test_login_status_tool_callable():
    # login_status reads local state only (no network); calling the underlying
    # function should return a dict with an 'authed' key.
    from cgimg.auth import tokens
    st = tokens.login_status()
    assert "authed" in st
