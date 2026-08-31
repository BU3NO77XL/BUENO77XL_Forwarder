# -*- coding: utf-8 -*-
"""Helpers de UI desacoplados."""
import asyncio
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt
from qasync import asyncSlot
from telegram_forwarder.ui.dialogs import CodeDialog, AsyncMessageBox
from telegram_forwarder.core.i18n import t

class UiHelpersMixin:
    def set_status(self, text, color):
        self.ui.lbl_status.setText('<p align="center"><b>{}</b></p>'.format(text))
        self.ui.lbl_status.setStyleSheet('color: {}; font-size: 14pt; font-weight: bold;'.format(color))

    def selected_phone(self):
        phone = self.ui.combo_select_account.currentData()
        if phone:
            return str(phone).strip()
        return self.ui.combo_select_account.currentText().strip()

    def _input_value(self, input_widget):
        return self._picked_ids.get(input_widget.objectName()) or input_widget.text().strip()

    def update_sync_label(self):
        from telegram_forwarder.core.forwarder import State
        phone = self.selected_phone()
        src = self._input_value(self.ui.source_channel_input)
        dst = self._input_value(self.ui.dest_channel_input)
        entry = {}
        if phone and src and dst:
            try:
                entry = State().get_entry_pair(phone, src, dst)
            except Exception:
                entry = {}
        if entry and entry.get('last_id'):
            self.ui.lbl_last_sync.setText(t('state_synced').format(entry.get('last_id'), entry.get('updated_at', '?')))
        else:
            self.ui.lbl_last_sync.setText(t('state_no_history'))

    def _on_source_changed(self):
        if not self._setting_text:
            self._picked_ids.pop(self.ui.source_channel_input.objectName(), None)
        self.update_sync_label()

    def _on_dest_changed(self):
        if not self._setting_text:
            self._picked_ids.pop(self.ui.dest_channel_input.objectName(), None)
        self.update_sync_label()

    @asyncSlot()
    async def ask_code_dialog(self, title, label):
        dlg = CodeDialog(t(title), t(label), self)
        dlg.setModal(True)
        dlg.show()
        while dlg.result() == 0:
            await asyncio.sleep(0.1)
        if dlg.result() == 1:
            return dlg.get_value(), True
        else:
            return "", False

    @asyncSlot()
    async def show_async_message(self, title, message, icon=QMessageBox.Icon.Information):
        dlg = AsyncMessageBox(title, message, icon, self)
        dlg.show()
        while dlg.result is None:
            await asyncio.sleep(0.05)
        return dlg

    def do_long_task(self):
        dlg = QProgressDialog(t('d_processing'), None, 0, 0, self)
        dlg.setWindowTitle(t('d_please_wait'))
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.show()
        return dlg
