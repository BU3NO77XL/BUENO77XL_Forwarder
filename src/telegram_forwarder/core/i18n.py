# -*- coding: utf-8 -*-
"""
i18n — traducoes da interface (EN / PT-BR).

Uso:
    from i18n import t, set_lang, get_lang
    set_lang('pt')
    t('btn_start')
"""

STRINGS = {
    'en': {
        'window_title': 'Telegram Restricted Channels Message Forwarder by BUENO77XL',
        'tab_account': '   Account   ',
        'tab_forward': '   Forward Messages   ',
        'ph_phone': '+123456789',
        'btn_add_account': 'Add account',
        'btn_remove_account': 'Remove account',
        'btn_update_number': 'Update Number',
        'lbl_add': 'Add:',
        'lbl_del': 'Del:',
        'help_add': '<p><b>This section is for adding an account.</b></p>',
        'help_remove': '<p><b>This section is for deleting an existing account in the program.</b></p>',
        'list_accounts_title': '<p align="center"><b>List Accounts</b></p>',
        'title_label': '<html><head/><body><p align="center"><span style=" font-size:18pt; font-weight:700; color:#4a90ff;">Restricted Channel to Channel Forwarder</span></p></body></html>',
        'lbl_select_account': 'Select Account:',
        'ph_combo_account': 'Choose an account to forward with...',
        'lbl_source': 'Source Channel:',
        'ph_source': '@durov or -1001234567890',
        'lbl_dest': 'Destination Channel:',
        'ph_dest': '@my_channel or -1009876543210',
        'btn_start': 'Start Forwarding',
        'btn_stop': 'Stop',
        'lbl_last_message': 'Last forwarded: No message yet',
        'state_no_history': 'State: no history — full history will be sent',
        'state_synced': 'State: synced up to id {} at {}',
        'lbl_success': 'Success:',
        'lbl_failed': 'Failed:',
        'lbl_total': 'Total:',
        'ph_log': 'Forwarding logs will appear here...\nExample: [2025-04-05 12:30:15] Message ID 1234 forwarded successfully',
        'tooltip_pick': 'Pick a channel/group from your account',
        'tooltip_lang': 'Language / Idioma',
        # status
        'st_active': 'Status: Active',
        'st_stopping': 'Status: Stopping...',
        'st_stopped': 'Status: Stopped',
        'st_finished': 'Status: Finished',
        'st_uptodate': 'Status: Up to date',
        'st_error': 'Status: Error',
        'st_invalid': 'Status: Invalid input',
        'st_floodwait': 'Status: FloodWait {}s',
        'st_session': 'Status: Session expired',
        'st_access': 'Status: Access denied',
        # dialogs
        'd_no_accounts': 'No accounts found.',
        'd_already': 'Already extracting.',
        'd_select_account': 'Select an account first.',
        'd_same': 'Source and destination must be different.',
        'd_invalid': 'Invalid Telegram link or chat id.',
        'd_not_active': 'Extraction is not active.',
        'd_floodwait': 'Telegram FloodWait: wait {} seconds and try again.',
        'd_floodwait_pick': 'Telegram FloodWait: try again in {}s.',
        'd_session': 'Session invalid/expired for {}.\nRemove and add the account again.',
        'd_private': 'Cannot access the channel.\nMake sure the account is a participant.',
        'd_unexpected': 'Unexpected error: {}',
        'd_timeout': 'Connection timed out. Check your internet/proxy.',
        'd_success_extracted': 'Extracted {} messages.',
        'd_pick_failed': 'Failed to list chats: {}',
        'd_pick_empty': 'No channels/groups found for this account.',
        'd_pick_active': 'Forwarding is active. Stop it first.',
        'd_phone_short': 'Phone number is too short.',
        'd_phone_invalid': "Phone number must start with '+' and contain only digits after it.",
        'd_phone_sample': 'Sample phone number is not allowed.',
        'd_login_code_title': 'Account login code',
        'd_enter_code': 'Enter the 5-digit code:',
        'd_password_title': 'Account password',
        'd_enter_password': 'Enter the password:',
        'd_cancelled': 'Canceled by user.',
        'd_invalid_code': 'Invalid code.',
        'd_invalid_password': 'Invalid password.',
        'd_account_removed': 'Account removed.',
        'd_account_not_found': 'Account not found.',
        'd_account_list_updated': 'Account list updated.',
        'd_processing': 'Processing ...',
        'd_please_wait': 'Please wait.',
        'd_login_success': 'Successfully logged in : {}',
        'd_account_exists': 'Account {} already exist',
        'd_account_data_missing': 'Account data not found for {} (data/{}.json missing).',
        'd_resolve_fail': 'Failed to join/resolve {}: {}',
        'code_ok': 'OK',
        'code_cancel': 'Cancel',
        'd_account_exist_now': 'Account {} already exists.',
        'd_logged_success': 'Successfully logged in: {}',
        # mensagens do backend (func.py) para mapeamento
        'backend_account_exist': 'Account {} already exist',
        'backend_logged_success': 'Successfully logged in : {}',
        't_error': 'Error',
        't_success': 'Success',
        't_wrong': 'Wrong',
        't_info': 'Info',
        # logs
        'l_extracting': 'Extracting {}...',
        'l_connected': 'Connected to {}.',
        'l_source': 'Source: {} (id {})',
        'l_destination': 'Destination: {} (id {})',
        'l_state_found': 'State found: last sent id={} (only new messages will be sent).',
        'l_no_state': 'No previous state: full history will be sent.',
        'l_indexing': 'Indexing source channel messages...',
        'l_stopped_user': 'Extraction stopped by user.',
        'l_no_new': 'No new messages found. Nothing to send.',
        'l_indexed': 'Indexed {} new message(s). Sending in chronological order (oldest -> newest)...',
        'l_done': 'Done. Sent {} message(s), {} failed.',
        'l_disconnected': 'Disconnected from {}.',
        'l_stop_req': 'Stop requested. Finishing current step...',
        'l_fatal': 'Fatal error: {}',
        'l_floodwait': 'FloodWait: Telegram asked to wait {}s. Try again later.',
        'l_session_err': 'Error: session for {} is invalid or expired. Re-add the account.',
        'l_private_err': 'Error: cannot access the channel (private/not a member?). {}',
        'l_last_fwd': 'Last forwarded: id={} at {}',
        # picker
        'p_source_title': 'Select source channel',
        'p_dest_title': 'Select destination channel',
        'p_search': '🔍 Search channel/group...',
    },
    'pt': {
        'window_title': 'Encaminhador de Mensagens de Canais Restritos do Telegram por BUENO77XL',
        'tab_account': '   Conta   ',
        'tab_forward': '   Encaminhar Mensagens   ',
        'ph_phone': '+123456789',
        'btn_add_account': 'Adicionar conta',
        'btn_remove_account': 'Remover conta',
        'btn_update_number': 'Atualizar Números',
        'lbl_add': 'Add:',
        'lbl_del': 'Del:',
        'help_add': '<p><b>Esta seção é para adicionar uma conta.</b></p>',
        'help_remove': '<p><b>Esta seção é para remover uma conta existente no programa.</b></p>',
        'list_accounts_title': '<p align="center"><b>Lista de Contas</b></p>',
        'title_label': '<html><head/><body><p align="center"><span style=" font-size:18pt; font-weight:700; color:#4a90ff;">Encaminhador de Canal Restrito para Canal</span></p></body></html>',
        'lbl_select_account': 'Selecionar Conta:',
        'ph_combo_account': 'Escolha uma conta para encaminhar...',
        'lbl_source': 'Canal de Origem:',
        'ph_source': '@durov ou -1001234567890',
        'lbl_dest': 'Canal de Destino:',
        'ph_dest': '@meu_canal ou -1009876543210',
        'btn_start': 'Iniciar Encaminhamento',
        'btn_stop': 'Parar',
        'lbl_last_message': 'Último encaminhado: Nenhuma mensagem ainda',
        'state_no_history': 'Estado: sem histórico — o histórico completo será enviado',
        'state_synced': 'Estado: sincronizado até o id {} em {}',
        'lbl_success': 'Sucesso:',
        'lbl_failed': 'Falhas:',
        'lbl_total': 'Total:',
        'ph_log': 'Os logs de encaminhamento aparecerão aqui...\nExemplo: [2025-04-05 12:30:15] Mensagem ID 1234 encaminhada com sucesso',
        'tooltip_pick': 'Escolher um canal/grupo da sua conta',
        'tooltip_lang': 'Language / Idioma',
        # status
        'st_active': 'Status: Ativo',
        'st_stopping': 'Status: Parando...',
        'st_stopped': 'Status: Parado',
        'st_finished': 'Status: Concluído',
        'st_uptodate': 'Status: Em dia',
        'st_error': 'Status: Erro',
        'st_invalid': 'Status: Entrada inválida',
        'st_floodwait': 'Status: FloodWait {}s',
        'st_session': 'Status: Sessão expirada',
        'st_access': 'Status: Acesso negado',
        # dialogs
        'd_no_accounts': 'Nenhuma conta encontrada.',
        'd_already': 'Já existe uma extração em andamento.',
        'd_select_account': 'Selecione uma conta primeiro.',
        'd_same': 'Origem e destino devem ser diferentes.',
        'd_invalid': 'Link do Telegram ou id de chat inválido.',
        'd_not_active': 'A extração não está ativa.',
        'd_floodwait': 'FloodWait do Telegram: aguarde {} segundos e tente novamente.',
        'd_floodwait_pick': 'FloodWait do Telegram: tente novamente em {}s.',
        'd_session': 'Sessão inválida/expirada para {}.\nRemova e adicione a conta novamente.',
        'd_private': 'Não foi possível acessar o canal.\nVerifique se a conta é participante.',
        'd_unexpected': 'Erro inesperado: {}',
        'd_timeout': 'Tempo de conexão esgotado. Verifique sua internet/proxy.',
        'd_success_extracted': '{} mensagens extraídas.',
        'd_pick_failed': 'Falha ao listar os chats: {}',
        'd_pick_empty': 'Nenhum canal/grupo encontrado para esta conta.',
        'd_pick_active': 'O encaminhamento está ativo. Pare primeiro.',
        'd_phone_short': 'O número de telefone é muito curto.',
        'd_phone_invalid': "O número deve começar com '+' e conter apenas dígitos depois.",
        'd_phone_sample': 'O número de exemplo não é permitido.',
        'd_login_code_title': 'Código de login da conta',
        'd_enter_code': 'Digite o código de 5 dígitos:',
        'd_password_title': 'Senha da conta',
        'd_enter_password': 'Digite a senha:',
        'd_cancelled': 'Cancelado pelo usuário.',
        'd_invalid_code': 'Código inválido.',
        'd_invalid_password': 'Senha inválida.',
        'd_account_removed': 'Conta removida.',
        'd_account_not_found': 'Conta não encontrada.',
        'd_account_list_updated': 'Lista de contas atualizada.',
        'd_processing': 'Processando ...',
        'd_please_wait': 'Por favor, aguarde.',
        'd_login_success': 'Logado com sucesso : {}',
        'd_account_exists': 'A conta {} já existe',
        'd_account_data_missing': 'Dados da conta {} não encontrados (data/{}.json ausente).',
        'd_resolve_fail': 'Falha ao entrar/resolver {}: {}',
        'code_ok': 'OK',
        'code_cancel': 'Cancelar',
        'd_account_exist_now': 'A conta {} já existe.',
        'd_logged_success': 'Logado com sucesso: {}',
        # mensagens do backend (func.py) para mapeamento
        'backend_account_exist': 'A conta {} já existe',
        'backend_logged_success': 'Logado com sucesso : {}',
        't_error': 'Erro',
        't_success': 'Sucesso',
        't_wrong': 'Errado',
        't_info': 'Info',
        # logs
        'l_extracting': 'Extraindo {}...',
        'l_connected': 'Conectado a {}.',
        'l_source': 'Origem: {} (id {})',
        'l_destination': 'Destino: {} (id {})',
        'l_state_found': 'Estado encontrado: última enviada id={} (apenas as novas serão enviadas).',
        'l_no_state': 'Sem estado anterior: o histórico completo será enviado.',
        'l_indexing': 'Indexando mensagens do canal de origem...',
        'l_stopped_user': 'Extração parada pelo usuário.',
        'l_no_new': 'Nenhuma mensagem nova. Nada para enviar.',
        'l_indexed': '{} nova(s) mensagem(ns) indexada(s). Enviando em ordem cronológica (antiga -> nova)...',
        'l_done': 'Concluído. {} mensagem(ns) enviada(s), {} falha(s).',
        'l_disconnected': 'Desconectado de {}.',
        'l_stop_req': 'Parada solicitada. Finalizando a etapa atual...',
        'l_fatal': 'Erro fatal: {}',
        'l_floodwait': 'FloodWait: o Telegram pediu para aguardar {}s. Tente mais tarde.',
        'l_session_err': 'Erro: sessão de {} inválida ou expirada. Adicione a conta novamente.',
        'l_private_err': 'Erro: não foi possível acessar o canal (privado/sem participação?). {}',
        'l_last_fwd': 'Último encaminhado: id={} às {}',
        # picker
        'p_source_title': 'Selecione o canal de origem',
        'p_dest_title': 'Selecione o canal de destino',
        'p_search': '🔍 Buscar canal/grupo...',
    },
}

_current = 'en'


def set_lang(lang):
    global _current
    _current = lang if lang in STRINGS else 'en'


def get_lang():
    return _current


def t(key):
    """Traduz a chave no idioma atual (fallback: ingles, depois a propria chave)."""
    return STRINGS.get(_current, {}).get(key) or STRINGS['en'].get(key, key)


# Mapeia mensagens do backend (func.py) em ingles para traducoes conhecidas
_BACKEND_MAP = {
    'backend_account_exist': 'd_account_exist_now',
    'backend_logged_success': 'd_logged_success',
}


def backend_message(msg):
    """
    Traduz uma mensagem vinda do func.py (backend).
    Se for uma das conhecidas (ex: 'Account X already exist'), traduz.
    Caso contrario, retorna a mensagem original (fallback).
    """
    if not msg:
        return msg
    s = str(msg)
    for key, i18n_key in _BACKEND_MAP.items():
        template = STRINGS['en'].get(key, '')
        param = match_template(s, template)
        if param is not None:
            return t(i18n_key).format(param.strip())
    return s


def match_template(value, template):
    """Extrai o parametro entre o prefixo e o sufixo fixo do template (ou propria string se sem sufixo)."""
    if not template:
        return None
    parts = template.split('{}', 1)
    prefix = parts[0]
    if not value.startswith(prefix):
        return None
    # remove o prefixo do valor
    rest = value[len(prefix):]
    if len(parts) == 1:
        # template nao tem placeholder: casou exato?
        return rest if rest == '' else None
    # sufixo apos o placeholder (pode ser vazio)
    suffix = parts[1]
    if not suffix:
        return rest  # resto inteiro e o parametro
    if not rest.endswith(suffix):
        return None
    return rest[:-len(suffix)]
