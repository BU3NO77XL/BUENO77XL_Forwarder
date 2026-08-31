# -*- coding: utf-8 -*-
"""
forwarder_core.py — Logica compartilhada de encaminhamento com estado persistente.

Guarda em data/state.json o id da ultima mensagem JA ENVIADA de cada canal
de origem (por conta). Com isso, tanto a GUI (main.py) quanto o daemon
(daemon.py) conseguem:

  - Primeira execucao (sem estado): indexar e enviar o historico completo.
  - Execucoes seguintes: detectar e enviar apenas as mensagens NOVAS
    (id > last_id), em ordem cronologica.
  - Retomar de onde parou se o processo cair (estado salvo apos cada envio).

Para forcar o reenvio completo, apague data/state.json (ou a chave do canal).
"""

import os
import json
import random
import asyncio
from datetime import datetime

from pyrogram import errors
from .paths import STATE_FILE, ensure_runtime_dirs


def normalize_channel(text: str) -> str:
    """Normaliza o identificador do canal para usar como chave de estado.

    @Canal, @canal, t.me/canal e https://t.me/canal viram a mesma chave.
    Tokens de convite (t.me/+Token) e ids numericos (-100...) ficam intactos.
    """
    t = (text or '').strip()
    if not t:
        return ''
    low = t.lower()
    if low.startswith('https://t.me/'):
        t = t[len('https://t.me/'):]
    elif low.startswith('http://t.me/'):
        t = t[len('http://t.me/'):]
    elif low.startswith('t.me/'):
        t = t[len('t.me/'):]
    if t.startswith('@'):
        return t.lower()  # usernames sao case-insensitive
    if t.startswith('+'):
        return t  # token de convite: case-sensitive, manter como esta
    if t.lstrip('-').isdigit():
        return t  # id numerico do canal, manter como esta
    # username sem @ (ex: t.me/canal) -> tratar como @canal
    return '@' + t.lower()


class State:
    """Estado persistente: ultima mensagem enviada por (conta, canal de origem)."""

    def __init__(self, path=None):
        from pathlib import Path as _Path
        # STATE_FILE é Path; aceita str|Path e normaliza para Path
        self.path = _Path(path) if path is not None else _Path(STATE_FILE)
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            from pathlib import Path as _Path
            p = _Path(self.path)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = _Path(str(p) + '.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, p)  # gravacao atomica
        except Exception as e:
            print('[state] save error: {}'.format(e))

    def get_last_id(self, phone: str, fromchat: str) -> int:
        key = '{}|{}'.format(phone, normalize_channel(fromchat))
        try:
            return int(self._data.get(key, {}).get('last_id', 0))
        except Exception:
            return 0

    def get_entry(self, phone: str, fromchat: str) -> dict:
        """Retorna a entrada completa (last_id, dest, updated_at) ou {}."""
        key = '{}|{}'.format(phone, normalize_channel(fromchat))
        try:
            return dict(self._data.get(key, {}))
        except Exception:
            return {}

    def set_last_id(self, phone: str, fromchat: str, last_id: int, dest: str = '') -> None:
        key = '{}|{}'.format(phone, normalize_channel(fromchat))
        self._data[key] = {
            'last_id': int(last_id),
            'dest': dest,
            'updated_at': datetime.now().isoformat(timespec='seconds'),
        }
        self._save()

    # ------------------------------------------------------------
    # Chave por (conta, origem, destino): permite enviar o MESMO canal
    # de origem para VARIOS destinos, cada um com seu proprio estado.
    # ------------------------------------------------------------
    @staticmethod
    def _pair_key(phone: str, fromchat: str, dest: str) -> str:
        return '{}|{}|{}'.format(
            phone, normalize_channel(fromchat), normalize_channel(dest)
        )

    def get_last_id_pair(self, phone: str, fromchat: str, dest: str) -> int:
        """
        Busca o last_id pela chave (conta|origem|destino).
        Fallback: se nao existir, tenta a chave legada (conta|origem) — mas so
        se o destino da entrada legada for o MESMO destino solicitado (assim,
        trocar de destino comeca do zero, como esperado).
        """
        entry = self._data.get(self._pair_key(phone, fromchat, dest))
        if entry:
            try:
                return int(entry.get('last_id', 0))
            except Exception:
                return 0
        # fallback: chave legada (só origem) — apenas se o destino casar
        legacy = self.get_entry(phone, fromchat)
        if legacy and legacy.get('last_id'):
            legacy_dest = normalize_channel(str(legacy.get('dest', '')))
            if legacy_dest and legacy_dest == normalize_channel(dest):
                try:
                    return int(legacy.get('last_id', 0))
                except Exception:
                    return 0
        return 0

    def get_entry_pair(self, phone: str, fromchat: str, dest: str) -> dict:
        """Entrada completa pela chave (conta|origem|destino), com fallback legado."""
        entry = self._data.get(self._pair_key(phone, fromchat, dest))
        if entry:
            try:
                return dict(entry)
            except Exception:
                return {}
        return self.get_entry(phone, fromchat)

    def set_last_id_pair(self, phone: str, fromchat: str, dest: str, last_id: int) -> None:
        """Salva o last_id na chave (conta|origem|destino)."""
        self._data[self._pair_key(phone, fromchat, dest)] = {
            'last_id': int(last_id),
            'dest': normalize_channel(dest),
            'updated_at': datetime.now().isoformat(timespec='seconds'),
        }
        self._save()


async def fetch_new_ids(cli, chat_id, last_id, log=print):
    """
    Retorna (ordenado do mais antigo para o mais novo) os ids das mensagens
    com id > last_id. Se last_id == 0, retorna o historico completo.
    Usa apenas min_id (offset_id deprecated) e ignora service messages.
    """
    ids = []
    # min_id no get_chat_history é tratado como inclusivo (min_id-1 interno),
    # então last_id+1 garante id > last_id sem deprecation de offset_id
    target_min = (last_id + 1) if last_id else 0
    while True:
        try:
            async for m in cli.get_chat_history(chat_id=chat_id, min_id=target_min):
                if getattr(m, 'empty', False) or getattr(m, 'service', False) or m.id < 1:
                    continue
                if m.id <= last_id:
                    continue
                ids.append(m.id)
            break
        except errors.FloodWait as e:
            log('FloodWait while indexing: {}s'.format(e.value))
            await asyncio.sleep(e.value + random.randint(10, 35))
        except Exception as e:
            log('Error indexing: {}'.format(e))
            break
    return sorted(set(ids))


async def get_message_safe(cli, chat_id, message_id, log=print):
    """Busca uma mensagem pelo id, tratando FloodWait."""
    try:
        return await cli.get_messages(chat_id, message_id)
    except errors.FloodWait as e:
        log('FloodWait: {}'.format(e.value))
        await asyncio.sleep(e.value + random.randint(10, 35))
        try:
            return await cli.get_messages(chat_id, message_id)
        except Exception:
            return None
    except Exception as e:
        log('Error fetching {}: {}'.format(message_id, e))
        return None


async def _download_safe(m, timeout=180, retries=3, log=print):
    """Baixa mídia com timeout e retry para evitar 'upload.GetFile timed out'."""
    for attempt in range(1, retries + 1):
        try:
            # m.download já tem retry interno, mas envolvemos com wait_for para timeout maior
            path = await asyncio.wait_for(m.download(), timeout=timeout)
            if path and os.path.exists(path):
                return path
            if path is None and attempt < retries:
                log(f"Download retornou None id={getattr(m, 'id', '?')} tentativa {attempt}/{retries}")
                await asyncio.sleep(2 * attempt)
                continue
            if path:
                return path
        except asyncio.TimeoutError:
            log(f"Timeout baixando mídia id={getattr(m, 'id', '?')} tentativa {attempt}/{retries}")
            await asyncio.sleep(2 * attempt)
        except Exception as e:
            # Timeout de rede do pyrogram vem como Exception com 'timed out'
            if 'timed out' in str(e).lower() and attempt < retries:
                log(f"Retrying download id={getattr(m, 'id', '?')} ({attempt}/{retries}): {e}")
                await asyncio.sleep(3 * attempt)
                continue
            raise
    raise asyncio.TimeoutError(f"Falha ao baixar mídia id={getattr(m, 'id', '?')} após {retries} tentativas")


async def send_one(cli, dest_chat_id, m):
    """Envia uma mensagem tratando todos os tipos de midia."""
    # service/empty não podem ser copiados
    if getattr(m, 'service', False) or getattr(m, 'empty', False):
        return
    if m.text:
        await cli.send_message(
            chat_id=dest_chat_id,
            text=m.text,
            entities=m.entities,
            disable_web_page_preview=True
        )
    elif m.photo:
        path = await _download_safe(m)
        await cli.send_photo(
            chat_id=dest_chat_id,
            photo=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    elif m.video:
        path = await _download_safe(m)
        await cli.send_video(
            chat_id=dest_chat_id,
            video=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
            duration=m.video.duration,
            width=m.video.width,
            height=m.video.height,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    elif m.document:
        path = await _download_safe(m)
        await cli.send_document(
            chat_id=dest_chat_id,
            document=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    elif m.audio:
        path = await _download_safe(m)
        await cli.send_audio(
            chat_id=dest_chat_id,
            audio=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
            duration=m.audio.duration,
            performer=m.audio.performer,
            title=m.audio.title,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    elif m.animation:
        path = await _download_safe(m)
        await cli.send_animation(
            chat_id=dest_chat_id,
            animation=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
            duration=m.animation.duration,
            width=m.animation.width,
            height=m.animation.height,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    elif m.voice:
        path = await _download_safe(m)
        await cli.send_voice(
            chat_id=dest_chat_id,
            voice=path,
            caption=m.caption,
            caption_entities=m.caption_entities,
            duration=m.voice.duration,
        )
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    else:
        await m.copy(dest_chat_id)


async def send_with_retry(cli, dest_chat_id, m, log=print):
    """Envia com 1 retry apos FloodWait. Retorna True se enviado com sucesso."""
    try:
        await send_one(cli, dest_chat_id, m)
        return True
    except errors.FloodWait as e:
        log('FloodWait: {}'.format(e.value))
        await asyncio.sleep(e.value + random.randint(10, 35))
        try:
            await send_one(cli, dest_chat_id, m)
            return True
        except Exception as e2:
            log('Error sending [{}]: {}'.format(getattr(m, 'id', '?'), e2))
            return False
    except Exception as e:
        log('Error sending [{}]: {}'.format(getattr(m, 'id', '?'), e))
        return False