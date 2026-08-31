import sys
import os
if __package__ is None or __package__ == '':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qasync import QEventLoop

from telegram_forwarder.core.paths import ICON_FILE, ensure_runtime_dirs
from telegram_forwarder.ui.theme.dark import apply_windows_dark

ICON_PATH = str(ICON_FILE)
ensure_runtime_dirs()

# Estado global (compartilhado com mixins via import telegram_forwarder.app)
Status = False
Extract = False

# Re-export para compatibilidade (antigo app.py expunha)
COLOR_ACTIVE = '#00ff88'
COLOR_STOPPED = '#ff5555'
COLOR_ERROR = '#ffaa00'
COLOR_INFO = '#4a90ff'

# Janela modularizada
from telegram_forwarder.ui.main_window import MainWindow  # noqa: E402

__all__ = ["MainWindow", "main", "ICON_PATH", "Status", "Extract", "COLOR_ACTIVE", "COLOR_STOPPED", "COLOR_ERROR", "COLOR_INFO"]

def main():
    app = QApplication(sys.argv)
    apply_windows_dark(app)
    app.setWindowIcon(QIcon(ICON_PATH))
    loop = QEventLoop(app)
    import asyncio
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
