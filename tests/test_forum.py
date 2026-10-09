# -*- coding: utf-8 -*-
"""Testes da camada de forum sem conexao com o Telegram."""
import os
import pathlib
import sys
import tempfile
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from telegram_forwarder.core.forum import (  # noqa: E402
    ensure_topic_map,
    is_forum_chat,
    message_topic_id,
)
from telegram_forwarder.core import forum  # noqa: E402
from telegram_forwarder.core.forwarder import State  # noqa: E402


class FakeForumClient:
    def __init__(self):
        self.topics = {
            10: [
                SimpleNamespace(id=20, title='Noticias', date=20, icon_emoji_id='12345'),
                SimpleNamespace(id=1, title='General', date=1),
                SimpleNamespace(id=19, title='Antigo', date=10),
            ],
            11: [SimpleNamespace(id=1, title='General')],
        }
        self.created = []

    def get_forum_topics(self, chat_id):
        async def result():
            return self.topics[chat_id]

        return result()

    async def create_forum_topic(self, chat_id, title):
        new_id = 100 + len(self.created)
        self.created.append((chat_id, title))
        return SimpleNamespace(id=new_id, title=title)


class PremiumFallbackClient(FakeForumClient):
    async def create_forum_topic(self, chat_id, title, **kwargs):
        if 'icon_emoji_id' in kwargs:
            raise RuntimeError('Telegram says: [403 PREMIUM_ACCOUNT_REQUIRED]')
        return await super().create_forum_topic(chat_id, title)


def test_forum_detection_and_message_topic_fallbacks():
    assert is_forum_chat(SimpleNamespace(is_forum=True)) is True
    assert is_forum_chat(SimpleNamespace(is_forum=False)) is False
    assert is_forum_chat(SimpleNamespace(type=SimpleNamespace(name='FORUM'))) is True
    assert message_topic_id(SimpleNamespace(message_thread_id=42)) == 42
    assert message_topic_id(SimpleNamespace(reply_to_top_message_id=43)) == 43
    assert message_topic_id(SimpleNamespace()) == 1


def test_topic_map_reuses_existing_and_paces_topic_creation(monkeypatch):
    tmp = tempfile.mkdtemp()
    state = State(path=os.path.join(tmp, 'state.json'))
    cli = FakeForumClient()
    monkeypatch.setenv('SEND_DELAY_MIN', '0.5')
    monkeypatch.setenv('SEND_DELAY_MAX', '0.5')
    delays = []

    async def record_sleep(delay):
        delays.append(delay)

    with patch.object(forum.asyncio, 'sleep', record_sleep):
        mapping = asyncio.run(ensure_topic_map(cli, 10, 11, state, '+1', '10', '11'))

    assert mapping == {'1': 1, '19': 100, '20': 101}
    assert cli.created == [(11, 'Antigo'), (11, 'Noticias')]
    assert delays == [0.5]
    assert state.get_topic_map_pair('+1', '10', '11') == mapping


def test_last_id_update_preserves_topic_map():
    tmp = tempfile.mkdtemp()
    state = State(path=os.path.join(tmp, 'state.json'))
    state.set_topic_map_pair('+1', '10', '11', {'20': 100})
    state.set_last_id_pair('+1', '10', '11', 55)

    assert state.get_last_id_pair('+1', '10', '11') == 55
    assert state.get_topic_map_pair('+1', '10', '11') == {'20': 100}


def test_custom_icon_falls_back_without_premium():
    tmp = tempfile.mkdtemp()
    state = State(path=os.path.join(tmp, 'state.json'))
    cli = PremiumFallbackClient()

    mapping = asyncio.run(ensure_topic_map(cli, 10, 11, state, '+1', '10', '11'))

    assert mapping['20'] == 101
