# -*- coding: utf-8 -*-
"""
daemon.py — Modo headless (sem interface grafica) para rodar na VPS.

Verifica o canal de origem periodicamente e encaminha apenas as mensagens
NOVAS para o canal de destino, usando o mesmo estado persistente da GUI
(data/state.json). Como voce ja enviou o historico completo localmente,
basta copiar a pasta do projeto (com account/, data/ e .env) para a VPS
que o daemon continuara de onde a GUI parou.

Configuracao no arquivo .env (veja .env.example):

    API_ID=1234567
    API_HASH=xxxx
    PHONE=+5511999999999           (numero de exemplo; use o SEU numero real no .env local)
    FROM_CHAT=@canal_origem        (ou -100xxxxxxxxxx)
    TO_CHAT=@canal_destino         (ou -100xxxxxxxxxx)
    CHECK_INTERVAL=120             (segundos entre verificacoes)

Uso:
    python daemon.py

Recomendado rodar com systemd (veja DEPLOY_VPS.md) para reiniciar
automaticamente em caso de queda.
"""

import os
import sys
import asyncio
import random
import traceback
from datetime import datetime

from telegram_forwarder.core.telegram import load_env, telegram_panel
from telegram_forwarder.core.forwarder import (
    State, fetch_new_ids, get_message_safe, send_pacing_delay, send_with_retry,
)
from telegram_forwarder.core.forum import ensure_topic_map, is_forum_chat, message_topic_id
from pyrogram import Client, errors

load_env()

API_ID = os.environ.get('API_ID', '').strip()
API_HASH = os.environ.get('API_HASH', '').strip()
PHONE = os.environ.get('PHONE', '').strip()
FROM_CHAT = os.environ.get('FROM_CHAT', '').strip()
TO_CHAT = os.environ.get('TO_CHAT', '').strip()
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '120').strip() or '120')

from telegram_forwarder.core.paths import ensure_runtime_dirs
ensure_runtime_dirs()


def log(msg):
    print('[{}] {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg), flush=True)


def validate_env():
    problems = []
    if not API_ID or not API_ID.isdigit():
        problems.append('API_ID invalido ou ausente no .env')
    if not API_HASH:
        problems.append('API_HASH ausente no .env')
    if not PHONE:
        problems.append('PHONE ausente no .env (ex: PHONE=+5511999999999)')
    if not FROM_CHAT:
        problems.append('FROM_CHAT ausente no .env (ex: FROM_CHAT=@canal_origem)')
    if not TO_CHAT:
        problems.append('TO_CHAT ausente no .env (ex: TO_CHAT=@canal_destino)')
    if problems:
        for p in problems:
            log('ERRO: {}'.format(p))
        log('Copie .env.example para .env e preencha as variaveis.')
        sys.exit(1)


async def resolve_chat(cli, link):
    """Resolve o canal de origem/destino. Retorna (chat_id, titulo) ou None."""
    if link.startswith('-100') and link.replace('-100', '').isdigit():
        try:
            c = await cli.get_chat(int(link))
            return c.id, c.title
        except Exception as e:
            log('Erro ao resolver {}: {}'.format(link, e))
            return None
    join = await telegram_panel.Join(cli, link)
    if len(join) != 3:
        log('Falha ao entrar/resolver o canal {}: {}'.format(link, join[0] if join else '?'))
        return None
    return join[0], join[1]


async def run_cycle():
    """Uma passada completa: conecta, verifica novas mensagens, envia, desconecta."""
    data = telegram_panel.get_json_data(PHONE)
    if not data:
        log('Conta {} nao encontrada (data/{}.json). Copie a pasta account/ e data/ da maquina local.'.format(PHONE, PHONE))
        return

    proxy = await telegram_panel.get_proxy(data.get('proxy', ''))
    from telegram_forwarder.core.paths import ACCOUNT_DIR
    cli = Client(str(ACCOUNT_DIR / PHONE), data['api_id'], data['api_hash'], proxy=proxy[0])
    try:
        await asyncio.wait_for(cli.connect(), 30)
        log('Conectado a {}.'.format(PHONE))

        src = await resolve_chat(cli, FROM_CHAT)
        if src is None:
            return
        dst = await resolve_chat(cli, TO_CHAT)
        if dst is None:
            return
        chat_id, dest_id = src[0], dst[0]

        # O daemon antigo continua igual para canais e grupos sem topicos.
        # O mapa so e criado quando os dois lados sao grupos-forum.
        source_chat = await cli.get_chat(chat_id)
        dest_chat = await cli.get_chat(dest_id)
        forum_mode = is_forum_chat(source_chat) and is_forum_chat(dest_chat)
        if forum_mode:
            log('Grupo-forum detectado. Os topicos serao recriados no destino.')
        else:
            log('Modo normal: origem/destino nao sao ambos grupos-forum.')

        state = State()
        # Chave por (conta, origem, destino): cada par tem seu proprio estado
        last_id = state.get_last_id_pair(PHONE, FROM_CHAT, TO_CHAT)
        topic_map = {}
        if forum_mode:
            topic_map = await ensure_topic_map(
                cli, chat_id, dest_id, state, PHONE, str(chat_id), str(dest_id), log=log
            )
        if last_id > 0:
            log('Estado encontrado: ultima enviada id={} (somente novas serao enviadas).'.format(last_id))
        else:
            log('Sem estado anterior: o historico completo sera enviado.')

        new_ids = await fetch_new_ids(cli, chat_id, last_id, log=log)
        total = len(new_ids)
        if total == 0:
            log('Nenhuma mensagem nova.')
            return

        log('{} nova(s) mensagem(ns) detectada(s). Enviando...'.format(total))
        ok = 0
        bad = 0
        copied_albums = set()
        failed_albums = set()
        for i, mid in enumerate(new_ids, 1):
            m = await get_message_safe(cli, chat_id, mid, log=log)
            if m is None or getattr(m, 'empty', False):
                continue
            media_group_id = getattr(m, 'media_group_id', None)
            if forum_mode and media_group_id in copied_albums:
                state.set_last_id_pair(PHONE, FROM_CHAT, TO_CHAT, mid)
                continue
            topic_id = None
            if forum_mode:
                topic_id = topic_map.get(str(message_topic_id(m)))
                if topic_id is None:
                    log('Topico de origem nao mapeado; mensagem id={} ignorada.'.format(mid))
                    bad += 1
                    continue
                # O General e o destino padrao; nao precisa de thread id.
                if topic_id == 1:
                    topic_id = None
            copy_album = bool(forum_mode and media_group_id and media_group_id not in failed_albums)
            sent = await send_with_retry(
                cli, dest_id, m, log=log, message_thread_id=topic_id,
                source_chat_id=chat_id, prefer_copy=forum_mode, copy_album=copy_album,
            )
            if not sent and copy_album:
                failed_albums.add(media_group_id)
                log('Album nao pode ser copiado como grupo; usando envio individual group_id={}'.format(media_group_id))
                sent = await send_with_retry(
                    cli, dest_id, m, log=log, message_thread_id=topic_id,
                    source_chat_id=chat_id, prefer_copy=False,
                )
            if sent:
                ok += 1
                if copy_album:
                    copied_albums.add(media_group_id)
                state.set_last_id_pair(PHONE, FROM_CHAT, TO_CHAT, mid)
            else:
                bad += 1
            log('[{}/{}] id={} ok={} falha={}'.format(i, total, mid, ok, bad))
            await asyncio.sleep(send_pacing_delay())
        log('Ciclo concluido: {} enviada(s), {} falha(s).'.format(ok, bad))
    finally:
        try:
            await cli.disconnect()
        except Exception:
            pass
        log('Desconectado.')


async def main():
    validate_env()
    log('Daemon iniciado. Conta={} Origem={} Destino={} Intervalo={}s'.format(PHONE, FROM_CHAT, TO_CHAT, CHECK_INTERVAL))
    while True:
        try:
            await run_cycle()
        except errors.FloodWait as e:
            log('FloodWait global: {}s'.format(e.value))
            await asyncio.sleep(e.value + random.randint(10, 35))
        except Exception as e:
            log('Erro no ciclo: {}'.format(e))
            traceback.print_exc()
        await asyncio.sleep(CHECK_INTERVAL + random.randint(0, 15))


def start():
    """Entry-point sincrono para console_scripts (evita RuntimeWarning: coroutine was never awaited)."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log('Encerrado pelo usuario.')


if __name__ == '__main__':
    start()
