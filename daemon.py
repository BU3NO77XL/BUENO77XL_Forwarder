# Wrapper — use `uv run tg-daemon` ou `python -m telegram_forwarder.daemon.daemon`
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
from telegram_forwarder.daemon.daemon import main
import asyncio
if __name__ == "__main__":
    asyncio.run(main())
