import importlib
import pathlib

ADAPTERS_DIR = pathlib.Path(__file__).parent / "adapters"

CLIENT_MAP = {}

if ADAPTERS_DIR.exists():
    for path in ADAPTERS_DIR.glob("*.py"):
        name = path.stem

        try:
            module = importlib.import_module(f".adapters.{name}", package=__name__)

            handler = getattr(module, "get_completion", None)
            CLIENT_MAP[name] = handler if callable(handler) else None

        except Exception as e:
            print(f"E: {e}")
            CLIENT_MAP[name] = None
