import asyncio
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import telegram_forwarder.core.forwarder as forwarder
from telegram_forwarder.core.forwarder import _download_timeout, _media_file_size, send_one
from telegram_forwarder.core.i18n import get_lang, set_lang, t


def test_large_document_gets_size_based_timeout():
    message = SimpleNamespace(document=SimpleNamespace(file_size=489721951))

    assert _media_file_size(message) == 489721951
    assert _download_timeout(message) == 1869


def test_photo_uses_largest_available_size():
    message = SimpleNamespace(photo=SimpleNamespace(sizes=[
        SimpleNamespace(file_size=1024),
        SimpleNamespace(file_size=2048),
    ]))

    assert _media_file_size(message) == 2048
    assert _download_timeout(message) == 180


def test_message_without_media_keeps_default_timeout():
    message = SimpleNamespace(text='plain text')

    assert _media_file_size(message) == 0
    assert _download_timeout(message) == 180


def test_send_one_uses_native_copy_when_available():
    class FakeClient:
        def __init__(self):
            self.copied = []

        async def copy_message(self, **kwargs):
            self.copied.append(kwargs)

    client = FakeClient()
    message = SimpleNamespace(id=65, text='hello', service=False, empty=False)

    asyncio.run(send_one(
        client, 2, message, source_chat_id=1, prefer_copy=True,
    ))

    assert client.copied == [{'chat_id': 2, 'from_chat_id': 1, 'message_id': 65}]


def test_last_sent_label_separates_queue_position_from_source_id():
    previous_lang = get_lang()
    try:
        set_lang('pt')
        label = t('l_last_fwd').format(4, 5175, 12, '12:30')

        assert 'item 4/5175' in label
        assert 'origem #12' in label
    finally:
        set_lang(previous_lang)


def test_temporary_download_is_cleaned_after_upload_failure():
    class FakeMessage:
        id = 65
        document = SimpleNamespace(file_size=12, file_name='archive.zip')

        async def download(self, file_name):
            with open(file_name, 'wb') as stream:
                stream.write(b'test payload')
            return file_name

    async def fail_upload(document, file_name, **kwargs):
        assert os.path.isfile(document)
        assert file_name == 'archive.zip'
        raise RuntimeError('upload failed')

    with tempfile.TemporaryDirectory() as temp_dir:
        previous_dir = forwarder.DOWNLOADS_DIR
        forwarder.DOWNLOADS_DIR = Path(temp_dir)
        logs = []
        try:
            async def run_transfer():
                await forwarder._send_media_file(
                    SimpleNamespace(send_document=fail_upload),
                    FakeMessage(),
                    'send_document',
                    'document',
                    {'chat_id': 1, 'file_name': 'archive.zip'},
                    log=logs.append,
                )

            try:
                asyncio.run(run_transfer())
            except RuntimeError as error:
                assert str(error) == 'upload failed'
            else:
                raise AssertionError('upload failure should be propagated')
            assert os.listdir(temp_dir) == []
            assert logs == [
                'Transferring file from source #65 (0.0 MiB).',
            ]
        finally:
            forwarder.DOWNLOADS_DIR = previous_dir