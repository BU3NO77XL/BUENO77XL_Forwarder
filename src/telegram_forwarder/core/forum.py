# -*- coding: utf-8 -*-
"""Compatibilidade de encaminhamento para grupos do Telegram com topicos."""


def is_forum_chat(chat) -> bool:
    """Detecta forum usando is_forum e o tipo, conforme a versao do cliente."""
    explicit = getattr(chat, 'is_forum', None)
    if explicit is not None:
        return bool(explicit)
    chat_type = getattr(chat, 'type', None)
    type_name = getattr(chat_type, 'name', chat_type)
    return str(type_name or '').upper() == 'FORUM'


def message_topic_id(message) -> int:
    """Extrai o id do topico de uma mensagem, usando General como fallback."""
    for name in ('message_thread_id', 'reply_to_top_message_id'):
        value = getattr(message, name, None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return 1


def topic_id(topic) -> int:
    """Aceita objetos de ForumTopic e respostas de bibliotecas compativeis."""
    for name in ('id', 'message_thread_id', 'top_message'):
        value = getattr(topic, name, None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    raise ValueError('Topico sem identificador')


def topic_title(topic) -> str:
    return str(getattr(topic, 'title', getattr(topic, 'name', '')) or '').strip()


def _topic_order_key(topic):
    """Ordena por criacao; o General permanece sempre em primeiro."""
    current_id = topic_id(topic)
    if current_id == 1:
        return (0, 0, 0)
    value = getattr(topic, 'date', 0)
    if hasattr(value, 'timestamp'):
        value = value.timestamp()
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0
    return (1, value, current_id)


def _optional_int(value):
    """Normaliza ids numericos vindos como str por algumas versoes do cliente."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def list_forum_topics(cli, chat_id):
    """Normaliza get_forum_topics(), async-iterator ou awaitable."""
    result = cli.get_forum_topics(chat_id)
    if hasattr(result, '__aiter__'):
        return [topic async for topic in result]
    result = await result
    if isinstance(result, (list, tuple)):
        return list(result)
    return list(getattr(result, 'topics', []) or [])


async def ensure_topic_map(cli, source_chat_id, dest_chat_id, state, phone, source_key, dest_key,
                           log=print):
    """Reutiliza/cria topicos por titulo e persiste o mapa no par."""
    mapping = state.get_topic_map_pair(phone, source_key, dest_key)
    source_topics = await list_forum_topics(cli, source_chat_id)
    source_topics.sort(key=_topic_order_key)
    dest_topics = await list_forum_topics(cli, dest_chat_id)
    by_title = {}
    for item in dest_topics:
        by_title.setdefault(topic_title(item).casefold(), []).append(topic_id(item))

    changed = False
    # Todo forum possui o topico Geral (id 1), embora algumas respostas da API
    # nao o incluam na listagem paginada.
    if mapping.get('1') != 1:
        mapping['1'] = 1
        changed = True
    for source_topic in source_topics:
        source_id = topic_id(source_topic)
        key = str(source_id)
        if key in mapping:
            continue
        if source_id == 1:
            mapping[key] = 1
            changed = True
            continue
        title = topic_title(source_topic)
        candidates = by_title.get(title.casefold(), [])
        if candidates:
            target_id = candidates.pop(0)
        else:
            create_kwargs = {}
            for attr in ('icon_color', 'icon_emoji_id'):
                value = _optional_int(getattr(source_topic, attr, None))
                if value is not None:
                    create_kwargs[attr] = value
            try:
                created = await cli.create_forum_topic(dest_chat_id, title, **create_kwargs)
            except TypeError:
                # Compatibilidade com versoes antigas sem suporte a icone.
                created = await cli.create_forum_topic(dest_chat_id, title)
            except Exception as exc:
                # Icones customizados podem exigir Telegram Premium. Re tenta
                # sem o emoji, preservando a criacao do topico e sua ordem.
                if 'PREMIUM_ACCOUNT_REQUIRED' not in str(exc) or 'icon_emoji_id' not in create_kwargs:
                    raise
                create_kwargs.pop('icon_emoji_id', None)
                log('Conta sem Premium; criando o topico sem icone personalizado: {}'.format(title))
                created = await cli.create_forum_topic(dest_chat_id, title, **create_kwargs)
            target_id = topic_id(created)
            log('Topico criado: {} -> {}'.format(title, target_id))
        mapping[key] = target_id
        changed = True

    if changed:
        state.set_topic_map_pair(phone, source_key, dest_key, mapping)
    return mapping
