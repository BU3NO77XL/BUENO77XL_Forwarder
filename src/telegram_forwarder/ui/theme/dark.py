# -*- coding: utf-8 -*-
"""Tema escuro — Fusion + palette para Windows (viewports brancos)."""
def apply_windows_dark(app):
    try:
        import sys as _sys
        if _sys.platform == "win32":
            app.setStyle("Fusion")
            from PyQt6.QtGui import QPalette, QColor
            pal = QPalette()
            pal.setColor(QPalette.ColorRole.Window, QColor("#1a1a1a"))
            pal.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
            pal.setColor(QPalette.ColorRole.Base, QColor("#2b2b2b"))
            pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#333333"))
            pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
            pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
            pal.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
            pal.setColor(QPalette.ColorRole.Button, QColor("#333333"))
            pal.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            pal.setColor(QPalette.ColorRole.BrightText, QColor("#ff5555"))
            pal.setColor(QPalette.ColorRole.Highlight, QColor("#357abd"))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            pal.setColor(QPalette.ColorRole.Link, QColor("#4a90ff"))
            app.setPalette(pal)
    except Exception:
        pass
