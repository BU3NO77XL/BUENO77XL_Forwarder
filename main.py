# Shim — mantido para compatibilidade. Código real em src/telegram_forwarder/app.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
from telegram_forwarder.app import main
if __name__ == "__main__":
    main()
