# -*- coding: utf-8 -*-
"""Janela principal — composição fina via mixins."""
from PyQt6.QtWidgets import QMainWindow
from telegram_forwarder.ui.panel import Ui_MainWindow
from .mixins.language import LanguageMixin
from .mixins.ui_helpers import UiHelpersMixin
from .mixins.client import ClientMixin
from .mixins.account import AccountMixin
from .mixins.picker import PickerMixin
from .mixins.forwarder import ForwarderMixin

class MainWindow(LanguageMixin, UiHelpersMixin, ClientMixin, AccountMixin, PickerMixin, ForwarderMixin, QMainWindow):
    def _setup_lang_icons(self):
        """Cria ícones de bandeira nativos para o botão toggle (sem dropdown)."""
        try:
            from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygon
            from PyQt6.QtCore import QPoint, Qt, QSize

            def us_icon():
                w, h = 20, 14
                pix = QPixmap(w, h)
                pix.fill(QColor("transparent"))
                p = QPainter(pix)
                p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                stripe_h = h / 7
                for i in range(7):
                    y = int(i * stripe_h)
                    hh = int(stripe_h + 0.5)
                    p.fillRect(0, y, w, hh, QColor("#B22234") if i % 2 == 0 else QColor("#FFFFFF"))
                canton_w = int(w * 0.4)
                canton_h = int(h * 0.54)
                p.fillRect(0, 0, canton_w, canton_h, QColor("#3C3B6E"))
                p.setBrush(QColor("#FFFFFF"))
                p.setPen(Qt.PenStyle.NoPen)
                for row in range(3):
                    for col in range(3):
                        if (row + col) % 2 == 0:
                            continue
                        sx = 3 + col * 4
                        sy = 2 + row * 3
                        p.drawEllipse(sx, sy, 1, 1)
                p.end()
                return QIcon(pix)

            def br_icon():
                w, h = 20, 14
                pix = QPixmap(w, h)
                pix.fill(QColor("#009739"))
                p = QPainter(pix)
                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                p.setBrush(QColor("#FEDF00"))
                p.setPen(Qt.PenStyle.NoPen)
                poly = QPolygon([QPoint(w // 2, 2), QPoint(w - 2, h // 2), QPoint(w // 2, h - 2), QPoint(2, h // 2)])
                p.drawPolygon(poly)
                p.setBrush(QColor("#002776"))
                r = 4
                p.drawEllipse(w // 2 - r, h // 2 - r, r * 2, r * 2)
                p.end()
                return QIcon(pix)

            self._lang_icons = {"en": us_icon(), "pt": br_icon()}
            self.ui.combo_lang.setIconSize(QSize(20, 14))
        except Exception:
            self._lang_icons = {}

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_lang_icons()
        self.setFixedSize(self.size())
        self.acclistupdate()
        self.ui.add_account.clicked.connect(self.add_account_proc)
        self.ui.remove_account_bot.clicked.connect(self.remove_account)
        self.ui.update_number_bot.clicked.connect(self.acclistupdate)
        self.ui.btn_start_forward.clicked.connect(self.forward_Channel)
        self.ui.btn_stop_forward.clicked.connect(self.disable_forward_Channel)
        self.ui.tab_account.currentChanged.connect(self.update_list_tab)
        self.ui.btn_pick_source.clicked.connect(self.pick_source_channel)
        self.ui.btn_pick_dest.clicked.connect(self.pick_dest_channel)
        self.ui.combo_lang.clicked.connect(self._on_lang_changed)
        self.ui.source_channel_input.textChanged.connect(self._on_source_changed)
        self.ui.dest_channel_input.textChanged.connect(self._on_dest_changed)
        self.ui.combo_select_account.currentTextChanged.connect(lambda _t: self.update_sync_label())
        self._picked_ids = {}
        self._setting_text = False
        self.apply_language()
        self.update_sync_label()
