# -*- coding: utf-8 -*-
"""Fábrica de cliente Telegram."""
import asyncio
from pyrogram import Client
from telegram_forwarder.core.telegram import telegram_panel
from telegram_forwarder.core.i18n import t

class ClientMixin:
    async def make_client(self, phone):
        data = telegram_panel.get_json_data(phone)
        if not data:
            raise RuntimeError(t('d_account_data_missing').format(phone, phone))
        proxy = await telegram_panel.get_proxy(data.get('proxy', ''))
        from telegram_forwarder.core.paths import ACCOUNT_DIR
        cli = Client(str(ACCOUNT_DIR / phone), data["api_id"], data["api_hash"], proxy=proxy[0])
        await asyncio.wait_for(cli.connect(), 20)
        return cli

    async def resolve_chat_obj(self, cli, link):
        t_ = (link or '').strip()
        if t_.lstrip('-').isdigit() and len(t_) >= 5:
            return await cli.get_chat(int(t_))
        join = await telegram_panel.Join(cli, t_)
        if len(join) != 3:
            raise RuntimeError(t('d_resolve_fail').format(t_, join[0] if join else '?'))
        return await cli.get_chat(join[0])
