# Shim compat — `src/telegram_forwarder/main.py` → `app.py`
import sys, pathlib
if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from telegram_forwarder.app import main, MainWindow  # noqa: F401
else:
    from .app import main, MainWindow  # noqa: F401

if __name__ == "__main__":
    main()

