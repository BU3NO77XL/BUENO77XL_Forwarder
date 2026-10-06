# -*- coding: utf-8 -*-
"""Lógica de encaminhamento."""
import asyncio
import traceback
import re
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from qasync import asyncSlot
from pyrogram import errors
from telegram_forwarder.core.telegram import telegram_panel
from telegram_forwarder.core.forwarder import (
    State, fetch_new_ids, get_message_safe, send_pacing_delay, send_with_retry,
)
from telegram_forwarder.core.forum import (
    ensure_topic_map,
    is_forum_chat,
    message_topic_id,
)
from telegram_forwarder.core.i18n import t

# cores
COLOR_ACTIVE = '#00ff88'
COLOR_STOPPED = '#ff5555'
COLOR_ERROR = '#ffaa00'

class ForwarderMixin:
    @asyncSlot()
    async def disable_forward_Channel(self):
        import telegram_forwarder.app as app_mod
        if app_mod.Extract:
            app_mod.Extract = False
            self.set_status(t('st_stopping'), COLOR_STOPPED)
            self.ui.forward_log.appendPlainText(t('l_stop_req'))
        else:
            await self.show_async_message(t('t_error'), t('d_not_active'), icon=QMessageBox.Icon.Critical)

    @asyncSlot()
    async def forward_Channel(self):
        import telegram_forwarder.app as app_mod
        self.ui.forward_log.clear()
        self.ui.forward_log.setReadOnly(True)
        if len(telegram_panel.list_accounts()) == 0:
            await self.show_async_message(t('t_error'), t('d_no_accounts'), icon=QMessageBox.Icon.Critical)
            return
        if app_mod.Extract:
            await self.show_async_message(t('t_error'), t('d_already'), icon=QMessageBox.Icon.Critical)
            return
        phone = self.selected_phone()
        if not phone:
            await self.show_async_message(t('t_error'), t('d_select_account'), icon=QMessageBox.Icon.Critical)
            return
        fromchat = self._input_value(self.ui.source_channel_input)
        forchat = self._input_value(self.ui.dest_channel_input)
        valid_src = telegram_panel.is_valid_telegram_link(fromchat) or telegram_panel.is_valid_chat_id(fromchat)
        valid_dst = telegram_panel.is_valid_telegram_link(forchat) or telegram_panel.is_valid_chat_id(forchat)
        if valid_src and valid_dst:
            if fromchat == forchat:
                await self.show_async_message(t('t_error'), t('d_same'), icon=QMessageBox.Icon.Critical)
                return
            app_mod.Extract = True
            self.set_status(t('st_active'), COLOR_ACTIVE)
            self.ui.btn_start_forward.setEnabled(False)
            asyncio.create_task(self.forward_proc(phone, fromchat, forchat))
        else:
            self.set_status(t('st_invalid'), COLOR_ERROR)
            await self.show_async_message(t('t_error'), t('d_invalid'), icon=QMessageBox.Icon.Critical)

    async def forward_proc(self, phone, fromchat, forchat):
        import telegram_forwarder.app as app_mod
        cli = None
        ana_count = 0
        okmsg = 0
        badmsg = 0
        try:
            self.ui.forward_log.appendPlainText(t('l_extracting').format(phone))
            try:
                cli = await self.make_client(phone)
            except asyncio.TimeoutError:
                raise RuntimeError(t('d_timeout'))
            self.ui.forward_log.appendPlainText(t('l_connected').format(phone))
            chat = await self.resolve_chat_obj(cli, fromchat)
            chatfor = await self.resolve_chat_obj(cli, forchat)
            self.ui.forward_log.appendPlainText(t('l_source').format(chat.title, chat.id))
            self.ui.forward_log.appendPlainText(t('l_destination').format(chatfor.title, chatfor.id))
            source_type = getattr(getattr(chat, 'type', None), 'name', getattr(chat, 'type', '?'))
            dest_type = getattr(getattr(chatfor, 'type', None), 'name', getattr(chatfor, 'type', '?'))
            self.ui.forward_log.appendPlainText(
                'Diagnostico: origem type={} is_forum={}; destino type={} is_forum={}'.format(
                    source_type, getattr(chat, 'is_forum', None),
                    dest_type, getattr(chatfor, 'is_forum', None),
                )
            )
            state = State()
            src_key = str(chat.id)
            dest_key = str(chatfor.id)
            forum_mode = is_forum_chat(chat) and is_forum_chat(chatfor)
            topic_map = {}
            if forum_mode:
                self.ui.forward_log.appendPlainText(t('l_forum_detected'))
                self.ui.forward_log.appendPlainText(t('l_forum_sync'))
                topic_map = await ensure_topic_map(
                    cli, chat.id, chatfor.id, state, phone, src_key, dest_key,
                    log=lambda s: self.ui.forward_log.appendPlainText(s),
                )
            else:
                self.ui.forward_log.appendPlainText(
                    'Modo normal: origem/destino nao foram identificados como grupos com topicos.'
                )
            last_id = state.get_last_id_pair(phone, src_key, dest_key)
            if last_id > 0:
                self.ui.forward_log.appendPlainText(t('l_state_found').format(last_id))
            else:
                self.ui.forward_log.appendPlainText(t('l_no_state'))
            self.ui.forward_log.appendPlainText(t('l_indexing'))
            all_ids = await fetch_new_ids(cli, chat.id, last_id, log=lambda s: self.ui.forward_log.appendPlainText(s))
            if app_mod.Extract == False:
                self.set_status(t('st_stopped'), COLOR_STOPPED)
                self.ui.forward_log.appendPlainText(t('l_stopped_user'))
                return
            all_ids = sorted(set(all_ids))
            total = len(all_ids)
            if total == 0:
                self.ui.forward_log.appendPlainText(t('l_no_new'))
                self.set_status(t('st_uptodate'), COLOR_ACTIVE)
                return
            self.ui.forward_log.appendPlainText(t('l_indexed').format(total))
            stopped = False
            copied_albums = set()
            failed_albums = set()
            for mid in all_ids:
                if app_mod.Extract == False:
                    stopped = True
                    break
                messagae = await get_message_safe(cli, chat.id, mid, log=lambda s: self.ui.forward_log.appendPlainText(s))
                if messagae is None or getattr(messagae, 'empty', False):
                    continue
                ana_count += 1
                media_group_id = getattr(messagae, 'media_group_id', None)
                if forum_mode and media_group_id in copied_albums:
                    state.set_last_id_pair(phone, src_key, dest_key, mid)
                    self.ui.forward_log.appendPlainText(
                        'Parte do album preservada: group_id={} id={}'.format(media_group_id, mid)
                    )
                    continue
                topic_id = None
                if forum_mode:
                    topic_id = topic_map.get(str(message_topic_id(messagae)))
                    if topic_id is None:
                        self.ui.forward_log.appendPlainText(
                            'Topico de origem nao mapeado; mensagem id={} ignorada.'.format(mid)
                        )
                        badmsg += 1
                        continue
                    # O General e o destino padrao; nao precisa de thread id.
                    if topic_id == 1:
                        topic_id = None
                copy_album = bool(forum_mode and media_group_id and media_group_id not in failed_albums)
                sent = await send_with_retry(
                    cli, chatfor.id, messagae,
                    log=lambda s: self.ui.forward_log.appendPlainText(s),
                    message_thread_id=topic_id,
                    source_chat_id=chat.id,
                    prefer_copy=forum_mode,
                    copy_album=copy_album,
                )
                if not sent and copy_album:
                    failed_albums.add(media_group_id)
                    self.ui.forward_log.appendPlainText(
                        'Album nao pode ser copiado como grupo; usando envio individual group_id={}'.format(media_group_id)
                    )
                    sent = await send_with_retry(
                        cli, chatfor.id, messagae,
                        log=lambda s: self.ui.forward_log.appendPlainText(s),
                        message_thread_id=topic_id,
                        source_chat_id=chat.id,
                        prefer_copy=False,
                    )
                if sent:
                    okmsg += 1
                    if copy_album:
                        copied_albums.add(media_group_id)
                    state.set_last_id_pair(phone, src_key, dest_key, mid)
                    self.ui.lbl_last_message.setText(t('l_last_fwd').format(mid, datetime.now().strftime('%H:%M:%S')))
                else:
                    badmsg += 1
                self.ui.success_count.display(okmsg)
                self.ui.failed_count.display(badmsg)
                self.ui.total_count.display(ana_count)
                self.ui.forward_log.appendPlainText("[{}/{}] id={}".format(ana_count, total, mid))
                await asyncio.sleep(send_pacing_delay())
            if stopped:
                self.set_status(t('st_stopped'), COLOR_STOPPED)
                self.ui.forward_log.appendPlainText(t('l_stopped_user'))
            else:
                self.set_status(t('st_finished'), COLOR_ACTIVE)
                self.ui.forward_log.appendPlainText(t('l_done').format(okmsg, badmsg))
                await self.show_async_message(t('t_success'), t('d_success_extracted').format(ana_count), icon=QMessageBox.Icon.Information)
            return
        except errors.FloodWait as e:
            self.set_status(t('st_floodwait').format(e.value), COLOR_ERROR)
            self.ui.forward_log.appendPlainText(t('l_floodwait').format(e.value))
            await self.show_async_message(t('t_error'), t('d_floodwait').format(e.value), icon=QMessageBox.Icon.Critical)
        except errors.Unauthorized:
            self.set_status(t('st_session'), COLOR_ERROR)
            self.ui.forward_log.appendPlainText(t('l_session_err').format(phone))
            await self.show_async_message(t('t_error'), t('d_session').format(phone), icon=QMessageBox.Icon.Critical)
        except errors.ChannelPrivate as e:
            self.set_status(t('st_access'), COLOR_ERROR)
            self.ui.forward_log.appendPlainText(t('l_private_err').format(e))
            await self.show_async_message(t('t_error'), t('d_private'), icon=QMessageBox.Icon.Critical)
        except asyncio.CancelledError:
            self.set_status(t('st_stopped'), COLOR_STOPPED)
        except Exception as e:
            self.set_status(t('st_error'), COLOR_ERROR)
            self.ui.forward_log.appendPlainText(t('l_fatal').format(e))
            traceback.print_exc()
            await self.show_async_message(t('t_error'), t('d_unexpected').format(e), icon=QMessageBox.Icon.Critical)
        finally:
            app_mod.Extract = False
            self.ui.btn_start_forward.setEnabled(True)
            if cli is not None:
                try: await cli.disconnect()
                except: pass
                self.ui.forward_log.appendPlainText(t('l_disconnected').format(phone))
            self.update_sync_label()

    def safe_filename(slef, name: str) -> str:
        name = re.sub(r'[<>:\"/\\|?*]', '_', name)
        name = name.strip().replace(' ', '_')
        return name or 'file'
