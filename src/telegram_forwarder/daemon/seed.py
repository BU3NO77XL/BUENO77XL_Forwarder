# -*- coding: utf-8 -*-
"""
seed_state.py — Marca o historico atual do canal como JA ENVIADO, sem reenviar.

Use isto UMA VEZ se voce ja enviou o historico completo manualmente (pela GUI
antiga, antes do estado persistente existir). Ele conecta, le o id da mensagem
mais recente do canal de origem e grava em data/state.json. A partir dai, a
GUI e o daemon so enviam mensagens postadas DEPOIS dessa marcacao.

Configuracao no .env (igual ao daemon.py):
    API_ID, API_HASH, PHONE, FROM_CHAT

Uso:
    python seed_state.py
"""

import os
import sys
import asyncio

from telegram_forwarder.core.telegram import load_env, telegram_panel
from telegram_forwarder.core.forwarder import State
from pyrogram import Client

load_env()

# Permite passar o canal como argumento: python seed_state.py @canal_origem
# Se nao passar, usa FROM_CHAT do .env
FROM_CHAT_ARG = sys.argv[1].strip() if len(sys.argv) > 1 else ''

API_ID = os.environ.get('API_ID', '').strip()
API_HASH = os.environ.get('API_HASH', '').strip()
PHONE = os.environ.get('PHONE', '').strip()
FROM_CHAT = FROM_CHAT_ARG or os.environ.get('FROM_CHAT', '').strip()

from telegram_forwarder.core.paths import ensure_runtime_dirs
ensure_runtime_dirs()


def log(msg):
    print(msg, flush=True)


async def main():
    if not PHONE:
        log('ERRO: preencha PHONE no .env (veja .env.example).')
        sys.exit(1)
    if not FROM_CHAT:
        log('ERRO: informe o canal de origem. Use: python seed_state.py @canal_origem')
        log('       ou preencha FROM_CHAT no .env.')
        sys.exit(1)

    data = telegram_panel.get_json_data(PHONE)
    if not data:
        log('ERRO: conta {} nao encontrada em data/. Copie account/ e data/ da maquina local.'.format(PHONE))
        sys.exit(1)

    proxy = await telegram_panel.get_proxy(data.get('proxy', ''))
    from telegram_forwarder.core.paths import ACCOUNT_DIR
    cli = Client(str(ACCOUNT_DIR / PHONE), data['api_id'], data['api_hash'], proxy=proxy[0])
    try:
        await asyncio.wait_for(cli.connect(), 30)
        log('Conectado a {}.'.format(PHONE))

        if FROM_CHAT.startswith('-100') and FROM_CHAT.replace('-100', '').isdigit():
            chat = await cli.get_chat(int(FROM_CHAT))
        else:
            join = await telegram_panel.Join(cli, FROM_CHAT)
            if len(join) != 3:
                log('ERRO: nao foi possivel resolver o canal {}: {}'.format(FROM_CHAT, join[0] if join else '?'))
                sys.exit(1)
            chat = await cli.get_chat(join[0])

        # Pega a mensagem mais recente do canal (historico vem do mais novo)
        latest_id = 0
        async for m in cli.get_chat_history(chat_id=chat.id, limit=1):
            latest_id = m.id

        if latest_id < 1:
            log('Nenhuma mensagem encontrada no canal. Nada para marcar.')
            return

        state = State()
        state.set_last_id(PHONE, FROM_CHAT, latest_id, os.environ.get('TO_CHAT', ''))
        log('Estado marcado: ultima mensagem do canal {} = id={}'.format(FROM_CHAT, latest_id))
        log('A partir de agora, apenas mensagens NOVAS (id > {}) serao enviadas.'.format(latest_id))
    finally:
        try:
            await cli.disconnect()
        except Exception:
            pass


def start():
    """Entry-point sincrono para console_scripts (evita RuntimeWarning: coroutine was never awaited)."""
    asyncio.run(main())


if __name__ == '__main__':
    start()