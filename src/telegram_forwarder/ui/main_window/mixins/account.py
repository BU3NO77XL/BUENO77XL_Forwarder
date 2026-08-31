# -*- coding: utf-8 -*-
"""Operações de conta."""
import asyncio
from PyQt6.QtWidgets import QMessageBox
from qasync import asyncSlot
from telegram_forwarder.core.telegram import telegram_panel
from telegram_forwarder.core.i18n import t, backend_message

class AccountMixin:
    @asyncSlot()
    async def load_account_display_names(self):
        combo = self.ui.combo_select_account
        for i in range(combo.count()):
            phone = combo.itemData(i)
            if not phone:
                continue
            phone = str(phone)
            data = telegram_panel.get_json_data(phone) or {}
            if data.get('username'):
                combo.setItemText(i, '@{}'.format(data['username']))
                continue
            cli = None
            try:
                cli = await self.make_client(phone)
                me = await cli.get_me()
                uname = getattr(me, 'username', None)
                if uname:
                    data['username'] = uname
                    telegram_panel.save_json_data(phone, data)
                    combo.setItemText(i, '@{}'.format(uname))
                else:
                    disp = me.first_name or phone
                    data['username'] = ''
                    data['display_name'] = disp
                    telegram_panel.save_json_data(phone, data)
                    combo.setItemText(i, str(disp))
            except Exception:
                pass
            finally:
                if cli is not None:
                    try: await cli.disconnect()
                    except: pass
                await asyncio.sleep(0.2)

    def refresh_account_combo_labels(self):
        combo = self.ui.combo_select_account
        for i in range(combo.count()):
            phone = combo.itemData(i)
            if not phone:
                continue
            data = telegram_panel.get_json_data(str(phone)) or {}
            uname = data.get('username')
            if uname:
                combo.setItemText(i, '@{}'.format(uname))

    def refresh_account_list_labels(self):
        r = telegram_panel.list_accounts()
        self.ui.list_account_ac.clear()
        for p in sorted(r):
            data = telegram_panel.get_json_data(p) or {}
            uname = data.get('username')
            label = '@{}'.format(uname) if uname else p
            self.ui.list_account_ac.addItem(label)
        self.ui.lcdNumber.display(len(r))

    def update_list_tab(self, index):
        if index == 0:
            self.refresh_account_list_labels()
        if index == 1:
            r = telegram_panel.list_accounts()
            self.ui.combo_select_account.clear()
            for p in r:
                self.ui.combo_select_account.addItem(p, p)
            self.refresh_account_combo_labels()
            if self.ui.combo_select_account.count() > 0 and self.ui.combo_select_account.currentIndex() < 0:
                self.ui.combo_select_account.setCurrentIndex(0)
            self.load_account_display_names()

    @asyncSlot()
    async def add_account_proc(self):
        phone = self.ui.account_input_add.text().strip()
        if len(phone) < 4:
            await self.show_async_message(t('t_wrong'), t('d_phone_short'), icon=QMessageBox.Icon.Critical)
            return
        if not phone.startswith("+") or not phone[1:].isdigit():
            await self.show_async_message(t('t_wrong'), t('d_phone_invalid'), icon=QMessageBox.Icon.Critical)
            return
        if phone == "+123456789":
            await self.show_async_message(t('t_wrong'), t('d_phone_sample'), icon=QMessageBox.Icon.Critical)
            return
        dlg = self.do_long_task()
        r = await telegram_panel.add_account(phone)
        dlg.close()
        if not r["status"]:
            await self.show_async_message(t('t_error'), backend_message(r["message"]), icon=QMessageBox.Icon.Critical)
            return
        for _ in range(3):
            text, ok = await self.ask_code_dialog("d_login_code_title", "d_enter_code")
            for _ in range(10):
                if not ok:
                    break
                if text.isdigit() and len(text) == 5:
                    break
                else:
                    text, ok = await self.ask_code_dialog("d_login_code_title", "d_enter_code")
            if not ok:
                await telegram_panel.cancel_acc(r["cli"], r["phone"])
                await self.show_async_message(t('t_error'), t('d_cancelled'), icon=QMessageBox.Icon.Critical)
                return
            dlg = self.do_long_task()
            rs = await telegram_panel.get_code(r["cli"], r["phone"], r["code_hash"], text)
            dlg.close()
            if rs["status"]:
                await self.show_async_message(t('t_success'), t('d_login_success').format(phone), icon=QMessageBox.Icon.Information)
                telegram_panel.make_json_data(r["phone"], r["api_id"], r["api_hash"], r["proxy"], "")
                return
            if rs["message"] == "invalid_code":
                await self.show_async_message(t('t_error'), t('d_invalid_code'), icon=QMessageBox.Icon.Critical)
                continue
            if rs["message"] == "FA2":
                for _ in range(3):
                    text, ok = await self.ask_code_dialog("d_password_title", "d_enter_password")
                    if not ok:
                        await telegram_panel.cancel_acc(r["cli"], r["phone"])
                        await self.show_async_message(t('t_error'), t('d_cancelled'), icon=QMessageBox.Icon.Critical)
                        return
                    dlg = self.do_long_task()
                    rsp = await telegram_panel.get_password(r["cli"], r["phone"], text)
                    dlg.close()
                    if rsp["status"]:
                        await self.show_async_message(t('t_success'), t('d_login_success').format(phone), icon=QMessageBox.Icon.Information)
                        telegram_panel.make_json_data(r["phone"], r["api_id"], r["api_hash"], r["proxy"], text)
                        return
                    if rsp["message"] == "invalid_password":
                        await self.show_async_message(t('t_error'), t('d_invalid_password'), icon=QMessageBox.Icon.Critical)
                        continue
                    else:
                        await self.show_async_message(t('t_error'), backend_message(rsp["message"]), icon=QMessageBox.Icon.Critical)
                        return
            if rs["message"]:
                await self.show_async_message(t('t_error'), backend_message(rs["message"]), icon=QMessageBox.Icon.Critical)
                return
        try: await telegram_panel.cancel_acc(r["cli"], r["phone"])
        except: pass
        await self.show_async_message(t('t_error'), t('d_cancelled'), icon=QMessageBox.Icon.Critical)

    def remove_account(self):
        phone = self.ui.remove_account_input.text().strip()
        if phone in telegram_panel.list_accounts():
            telegram_panel.remove_account(phone)
            QMessageBox.information(self, t('t_success'), t('d_account_removed'))
        else:
            QMessageBox.critical(self, t('t_error'), t('d_account_not_found'))

    def acclistupdate(self, log=True):
        r = telegram_panel.list_accounts()
        self.ui.list_account_ac.clear()
        self.ui.list_account_ac.addItems(r)
        self.ui.lcdNumber.display(len(r))
        if not log:
            QMessageBox.information(self, t('t_success'), t('d_account_list_updated'))
