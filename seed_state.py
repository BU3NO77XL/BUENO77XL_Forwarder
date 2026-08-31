# Wrapper — use `uv run tg-seed` ou `python -m telegram_forwarder.daemon.seed`
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import telegram_forwarder.daemon.seed as _seed
import asyncio
if __name__ == "__main__":
    asyncio.run(_seed.main())
