# -*- coding: utf-8 -*-
"""Mixin de idioma."""
from telegram_forwarder.core.i18n import t, set_lang, get_lang

COLOR_ACTIVE = '#00ff88'
COLOR_STOPPED = '#ff5555'
COLOR_ERROR = '#ffaa00'

class LanguageMixin:
    def _on_lang_changed(self, index):
        set_lang('pt' if 'PT-BR' in self.ui.combo_lang.currentText() else 'en')
        self.apply_language()

    def apply_language(self):
        self.setWindowTitle(t('window_title'))
        self.ui.tab_account.setTabText(self.ui.tab_account.indexOf(self.ui.Account), t('tab_account'))
        self.ui.tab_account.setTabText(self.ui.tab_account.indexOf(self.ui.ForwardTab), t('tab_forward'))
        self.ui.account_input_add.setPlaceholderText(t('ph_phone'))
        self.ui.add_account.setText(t('btn_add_account'))
        self.ui.remove_account_input.setPlaceholderText(t('ph_phone'))
        self.ui.remove_account_bot.setText(t('btn_remove_account'))
        self.ui.update_number_bot.setText(t('btn_update_number'))
        self.ui.help_account_add.setHtml(t('help_add'))
        self.ui.help_remove_account.setHtml(t('help_remove_account'))
        self.ui.label_add_account.setText(t('lbl_add'))
        self.ui.label_remove_account.setText(t('lbl_del'))
        self.ui.textBrowser_2.setHtml(t('list_accounts_title'))
        self.ui.label.setText(t('title_label'))
        self.ui.label1.setText(t('lbl_select_account'))
        self.ui.combo_select_account.setPlaceholderText(t('ph_combo_account'))
        self.ui.label2.setText(t('lbl_source'))
        self.ui.source_channel_input.setPlaceholderText(t('ph_source'))
        self.ui.label3.setText(t('lbl_dest'))
        self.ui.dest_channel_input.setPlaceholderText(t('ph_dest'))
        self.ui.btn_start_forward.setText(t('btn_start'))
        self.ui.btn_stop_forward.setText(t('btn_stop'))
        self.ui.lbl_last_message.setText(t('lbl_last_message'))
        self.ui.label4.setText(t('lbl_success'))
        self.ui.label5.setText(t('lbl_failed'))
        self.ui.label6.setText(t('lbl_total'))
        self.ui.forward_log.setPlaceholderText(t('ph_log'))
        self.ui.btn_pick_source.setToolTip(t('tooltip_pick'))
        self.ui.btn_pick_dest.setToolTip(t('tooltip_pick'))
        idx = 0 if get_lang() == 'en' else 1
        if self.ui.combo_lang.currentIndex() != idx:
            self.ui.combo_lang.setCurrentIndex(idx)
        self.update_sync_label()
        cur = self.ui.lbl_status.text()
        if 'Active' in cur or 'Ativo' in cur:
            self.set_status(t('st_active'), COLOR_ACTIVE)
        elif 'Up to date' in cur or 'Em dia' in cur:
            self.set_status(t('st_uptodate'), COLOR_ACTIVE)
        elif 'Finished' in cur or 'Concluído' in cur:
            self.set_status(t('st_finished'), COLOR_ACTIVE)
        elif 'Stopped' in cur or 'Parado' in cur:
            self.set_status(t('st_stopped'), COLOR_STOPPED)
        elif 'Stopping' in cur or 'Parando' in cur:
            self.set_status(t('st_stopping'), COLOR_STOPPED)
        elif 'Error' in cur or 'Erro' in cur:
            self.set_status(t('st_error'), COLOR_ERROR)
        elif 'Invalid' in cur or 'inválida' in cur:
            self.set_status(t('st_invalid'), COLOR_ERROR)
