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
import math
import shutil
import tempfile
from datetime import datetime

from pyrogram import errors
from .i18n import t
from .paths import DOWNLOADS_DIR, STATE_FILE, ensure_runtime_dirs


def send_pacing_delay() -> float:
    """Atraso aleatorio entre envios, configurado exclusivamente no .env."""
    raw_min = os.environ.get('SEND_DELAY_MIN', '').strip()
    raw_max = os.environ.get('SEND_DELAY_MAX', '').strip()
    if not raw_min or not raw_max:
        raise RuntimeError('SEND_DELAY_MIN e SEND_DELAY_MAX devem estar configurados no .env')
    try:
        lower = float(raw_min)
        upper = float(raw_max)
    except ValueError as exc:
        raise RuntimeError('SEND_DELAY_MIN e SEND_DELAY_MAX devem ser numeros') from exc
    if lower < 0 or upper < lower:
        raise RuntimeError('SEND_DELAY_MIN/MAX invalidos: use 0 <= MIN <= MAX')
    return random.uniform(lower, upper)


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

    def get_topic_map_pair(self, phone: str, fromchat: str, dest: str) -> dict:
        """Retorna o mapa de topicos do par, sem quebrar estados legados."""
        entry = self._data.get(self._pair_key(phone, fromchat, dest), {})
        topics = entry.get('topics', {}) if isinstance(entry, dict) else {}
        return dict(topics) if isinstance(topics, dict) else {}

    def set_topic_map_pair(self, phone: str, fromchat: str, dest: str, topics: dict) -> None:
        """Persiste o mapa origem-topic -> destino-topic do par."""
        key = self._pair_key(phone, fromchat, dest)
        entry = self._data.get(key, {})
        if not isinstance(entry, dict):
            entry = {}
        entry.update({
            'dest': normalize_channel(dest),
            'topics': dict(topics),
            'updated_at': datetime.now().isoformat(timespec='seconds'),
        })
        self._data[key] = entry
        self._save()

    def set_last_id_pair(self, phone: str, fromchat: str, dest: str, last_id: int) -> None:
        """Salva o last_id, preservando o mapa de topicos ja criado."""
        key = self._pair_key(phone, fromchat, dest)
        entry = self._data.get(key, {})
        if not isinstance(entry, dict):
            entry = {}
        entry.update({
            'last_id': int(last_id),
            'dest': normalize_channel(dest),
            'updated_at': datetime.now().isoformat(timespec='seconds'),
        })
        self._data[key] = entry
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
            log(t('l_floodwait_retry').format(e.value))
            await asyncio.sleep(e.value + random.randint(10, 35))
        except Exception as e:
            log(t('l_index_failed'))
            break
    return sorted(set(ids))


async def get_message_safe(cli, chat_id, message_id, log=print):
    """Busca uma mensagem pelo id, tratando FloodWait."""
    try:
        return await cli.get_messages(chat_id, message_id)
    except errors.FloodWait as e:
        log(t('l_floodwait_retry').format(e.value))
        await asyncio.sleep(e.value + random.randint(10, 35))
        try:
            return await cli.get_messages(chat_id, message_id)
        except Exception:
            return None
    except Exception as e:
        log(t('l_message_unavailable').format(message_id))
        return None


def _media_file_size(m):
    for media_type in ('photo', 'video', 'document', 'audio', 'animation', 'voice', 'video_note', 'sticker'):
        media = getattr(m, media_type, None)
        if media is None:
            continue
        size = getattr(media, 'file_size', None)
        if size:
            return int(size)
        if media_type == 'photo':
            sizes = getattr(media, 'sizes', ()) or ()
            return max((getattr(item, 'file_size', 0) or 0 for item in sizes), default=0)
    return 0


def _download_timeout(m, base_timeout=180):
    size = _media_file_size(m)
    # Allow two times the transfer time at 512 KiB/s for large files.
    size_timeout = math.ceil(size * 2 / (512 * 1024)) if size else 0
    return max(base_timeout, size_timeout)


def _media_extension(m):
    fallback_extensions = {
        'photo': '.jpg', 'video': '.mp4', 'document': '.bin', 'audio': '.mp3',
        'animation': '.mp4', 'voice': '.ogg', 'video_note': '.mp4', 'sticker': '.webp',
    }
    for media_type, fallback in fallback_extensions.items():
        media = getattr(m, media_type, None)
        if media is not None:
            file_name = os.path.basename(getattr(media, 'file_name', '') or '')
            extension = os.path.splitext(file_name)[1]
            return extension[:16] if extension else fallback
    return '.bin'


async def _download_safe(m, timeout=180, retries=3, log=print, download_dir=None,
                         progress=None):
    """Baixa mídia com timeout e retry para evitar 'upload.GetFile timed out'."""
    file_size = _media_file_size(m)
    download_timeout = _download_timeout(m, timeout)
    for attempt in range(1, retries + 1):
        try:
            # m.download já tem retry interno, mas envolvemos com wait_for para timeout maior
            download_kwargs = {}
            if download_dir:
                os.makedirs(download_dir, exist_ok=True)
                download_kwargs['file_name'] = os.path.join(
                    download_dir,
                    'message-{}-attempt-{}{}'.format(
                        getattr(m, 'id', 'unknown'), attempt, _media_extension(m),
                    ),
                )
            if progress is not None:
                download_kwargs['progress'] = progress
            path = await asyncio.wait_for(m.download(**download_kwargs), timeout=download_timeout)
            if path and os.path.exists(path):
                return path
            if path is None and attempt < retries:
                log(t('l_media_download_retry').format(
                    getattr(m, 'id', '?'), attempt + 1, retries,
                ))
                await asyncio.sleep(2 * attempt)
                continue
            if path:
                return path
        except asyncio.TimeoutError:
            if attempt < retries:
                log(t('l_media_download_timeout').format(
                    getattr(m, 'id', '?'), attempt + 1, retries,
                ))
            await asyncio.sleep(2 * attempt)
        except Exception as e:
            # Timeout de rede do pyrogram vem como Exception com 'timed out'
            if 'timed out' in str(e).lower() and attempt < retries:
                log(t('l_media_network_retry').format(
                    getattr(m, 'id', '?'), attempt + 1, retries,
                ))
                await asyncio.sleep(3 * attempt)
                continue
            raise
    raise asyncio.TimeoutError(
        t('l_media_download_failed').format(
            getattr(m, 'id', '?'), file_size / (1024 ** 2), retries,
        )
    )


async def _send_media_file(cli, m, send_method, file_arg, send_kwargs, log=print):
    file_size = _media_file_size(m)
    downloads_dir = str(DOWNLOADS_DIR)
    os.makedirs(downloads_dir, exist_ok=True)
    if file_size:
        reserve = min(64 * 1024 ** 2, max(8 * 1024 ** 2, file_size // 20))
        free_space = shutil.disk_usage(downloads_dir).free
        if free_space < file_size + reserve:
            raise OSError(
                t('l_media_disk_space').format(
                    getattr(m, 'id', '?'), file_size / (1024 ** 2),
                    free_space / (1024 ** 2),
                )
            )

    message_id = getattr(m, 'id', '?')
    with tempfile.TemporaryDirectory(prefix='forward-', dir=downloads_dir) as temp_dir:
        log(t('l_media_transfer_started').format(message_id, file_size / (1024 ** 2)))
        path = await _download_safe(
            m,
            log=log,
            download_dir=temp_dir,
        )
        if not path or not os.path.isfile(path):
            raise OSError(t('l_media_missing_file').format(message_id))
        await getattr(cli, send_method)(
            **send_kwargs,
            **{file_arg: path},
        )


async def send_one(cli, dest_chat_id, m, message_thread_id=None, source_chat_id=None,
                   prefer_copy=False, copy_album=False, log=print):
    """Envia uma mensagem tratando todos os tipos de midia."""
    topic_kwargs = {} if message_thread_id is None else {'message_thread_id': message_thread_id}
    # service/empty não podem ser copiados
    if getattr(m, 'service', False) or getattr(m, 'empty', False):
        return
    # Em forum, a copia nativa preserva formatacao, legenda, preview e midia.
    # Se falhar (por exemplo, conteudo protegido), usa o fallback manual abaixo.
    if prefer_copy and source_chat_id is not None and getattr(m, 'id', None):
        if copy_album and getattr(m, 'media_group_id', None):
            await cli.copy_media_group(
                chat_id=dest_chat_id,
                from_chat_id=source_chat_id,
                message_id=m.id,
                **topic_kwargs,
            )
            return
        try:
            await cli.copy_message(
                chat_id=dest_chat_id,
                from_chat_id=source_chat_id,
                message_id=m.id,
                **topic_kwargs,
            )
            return
        except Exception:
            pass
    if m.text:
        await cli.send_message(
            chat_id=dest_chat_id,
            text=m.text,
            entities=m.entities,
            disable_web_page_preview=True,
            **topic_kwargs,
        )
    elif m.photo:
        await _send_media_file(
            cli, m, 'send_photo', 'photo', {
                'chat_id': dest_chat_id,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                **topic_kwargs,
            }, log=log,
        )
    elif m.video:
        await _send_media_file(
            cli, m, 'send_video', 'video', {
                'chat_id': dest_chat_id,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                'duration': m.video.duration,
                'width': m.video.width,
                'height': m.video.height,
                **topic_kwargs,
            }, log=log,
        )
    elif m.document:
        await _send_media_file(
            cli, m, 'send_document', 'document', {
                'chat_id': dest_chat_id,
                'file_name': m.document.file_name,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                **topic_kwargs,
            }, log=log,
        )
    elif m.audio:
        await _send_media_file(
            cli, m, 'send_audio', 'audio', {
                'chat_id': dest_chat_id,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                'duration': m.audio.duration,
                'performer': m.audio.performer,
                'title': m.audio.title,
                **topic_kwargs,
            }, log=log,
        )
    elif m.animation:
        await _send_media_file(
            cli, m, 'send_animation', 'animation', {
                'chat_id': dest_chat_id,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                'duration': m.animation.duration,
                'width': m.animation.width,
                'height': m.animation.height,
                **topic_kwargs,
            }, log=log,
        )
    elif m.voice:
        await _send_media_file(
            cli, m, 'send_voice', 'voice', {
                'chat_id': dest_chat_id,
                'caption': m.caption,
                'caption_entities': m.caption_entities,
                'duration': m.voice.duration,
                **topic_kwargs,
            }, log=log,
        )
    else:
        copy_kwargs = {} if message_thread_id is None else {
            'reply_to_message_id': message_thread_id,
        }
        await m.copy(dest_chat_id, **copy_kwargs)


async def send_with_retry(cli, dest_chat_id, m, log=print, message_thread_id=None,
                          source_chat_id=None, prefer_copy=False, copy_album=False):
    """Envia com 1 retry apos FloodWait. Retorna True se enviado com sucesso."""
    try:
        await send_one(
            cli, dest_chat_id, m, message_thread_id=message_thread_id,
            source_chat_id=source_chat_id, prefer_copy=prefer_copy, copy_album=copy_album,
            log=log,
        )
        return True
    except errors.FloodWait as e:
        log(t('l_floodwait_retry').format(e.value))
        await asyncio.sleep(e.value + random.randint(10, 35))
        try:
            await send_one(
                cli, dest_chat_id, m, message_thread_id=message_thread_id,
                source_chat_id=source_chat_id, prefer_copy=prefer_copy, copy_album=copy_album,
                log=log,
            )
            return True
        except Exception:
            log(t('l_floodwait_failed').format(getattr(m, 'id', '?')))
            return False
    except Exception as e:
        log(t('l_send_failed').format(getattr(m, 'id', '?')))
        return False
