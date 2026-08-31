# -*- coding: utf-8 -*-
"""Entry-point para `python -m telegram_forwarder` (GUI)."""
from .app import MainWindow  # noqa
import sys

def main():
    from .app import main as _main
    _main()

if __name__ == "__main__":
    from .app import main as _main
    sys.exit(_main() if callable(_main) else 0)
