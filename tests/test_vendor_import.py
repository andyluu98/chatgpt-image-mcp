import os

# config.py instantiates `config = ConfigStore(...)` at import time and refuses
# to load without an auth-key. Set a dummy one so the vendored modules import.
# (Import resolution only — real auth is wired at runtime, not import time.)
os.environ.setdefault("CHATGPT2API_AUTH_KEY", "cgimg-import-test")

import cgimg._vendor_path  # noqa: E402,F401  (side effect: sys.path)


def test_backend_api_imports():
    import importlib
    mod = importlib.import_module("services.openai_backend_api")
    assert hasattr(mod, "OpenAIBackendAPI")


def test_conversation_imports():
    import importlib
    mod = importlib.import_module("services.protocol.conversation")
    assert hasattr(mod, "stream_image_outputs")


def test_image_storage_imports():
    import importlib
    mod = importlib.import_module("services.image_storage_service")
    assert hasattr(mod, "image_storage_service")
