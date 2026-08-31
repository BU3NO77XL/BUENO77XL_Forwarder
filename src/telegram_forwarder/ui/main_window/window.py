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
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
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
        self.ui.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        self.ui.source_channel_input.textChanged.connect(self._on_source_changed)
        self.ui.dest_channel_input.textChanged.connect(self._on_dest_changed)
        self.ui.combo_select_account.currentTextChanged.connect(lambda _t: self.update_sync_label())
        self._picked_ids = {}
        self._setting_text = False
        self.apply_language()
        self.update_sync_label()
