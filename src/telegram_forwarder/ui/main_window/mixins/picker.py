# -*- coding: utf-8 -*-
"""Picker de canais."""
import asyncio
from PyQt6.QtWidgets import QMessageBox
from qasync import asyncSlot
from pyrogram import errors
from telegram_forwarder.ui.dialogs import ChannelPickerDialog
from telegram_forwarder.core.i18n import t

class PickerMixin:
    @asyncSlot()
    async def pick_source_channel(self):
        await self._pick_channel(self.ui.source_channel_input, t('p_source_title'))

    @asyncSlot()
    async def pick_dest_channel(self):
        await self._pick_channel(self.ui.dest_channel_input, t('p_dest_title'))

    async def _pick_channel(self, target_input, title):
        from telegram_forwarder.app import Extract
        import telegram_forwarder.app as app_mod
        phone = self.selected_phone()
        if not phone:
            await self.show_async_message(t('t_error'), t('d_select_account'), icon=QMessageBox.Icon.Critical)
            return
        if app_mod.Extract:
            await self.show_async_message(t('t_error'), t('d_pick_active'), icon=QMessageBox.Icon.Critical)
            return
        dlg = self.do_long_task()
        cli = None
        picker = ChannelPickerDialog(title, self)
        picker.search.setPlaceholderText(t('p_search'))
        try:
            cli = await self.make_client(phone)
            async for d in cli.get_dialogs(limit=200):
                c = d.chat
                tname = getattr(c.type, 'name', '')
                if tname not in ('CHANNEL', 'SUPERGROUP', 'FORUM', 'GROUP'):
                    continue
                uname = getattr(c, 'username', None)
                value = '@' + uname if uname else str(c.id)
                title_txt = c.title or value
                label = '{}  —  {}'.format(title_txt, value)
                picker.add_item(label, (value, title_txt))
        except errors.FloodWait as e:
            await self.show_async_message(t('t_error'), t('d_floodwait_pick').format(e.value), icon=QMessageBox.Icon.Critical)
            return
        except Exception as e:
            await self.show_async_message(t('t_error'), t('d_pick_failed').format(e), icon=QMessageBox.Icon.Critical)
            return
        finally:
            if cli is not None:
                try: await cli.disconnect()
                except: pass
            dlg.close()
        if picker.listw.count() == 0:
            await self.show_async_message(t('t_error'), t('d_pick_empty'), icon=QMessageBox.Icon.Critical)
            return
        picker.show()
        while picker.result() == 0:
            await asyncio.sleep(0.1)
        if picker.result() == 1:
            sel = picker.get_selected()
            if sel:
                internal, display = sel
                self._setting_text = True
                target_input.setText(display)
                self._setting_text = False
                self._picked_ids[target_input.objectName()] = internal
                self.update_sync_label()
