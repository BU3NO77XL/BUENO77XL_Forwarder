# -*- coding: utf-8 -*-
"""Teste rapido do estado persistente (forwarder_core.State)."""
import os
import sys
import tempfile
import pathlib

# Usa um arquivo de estado temporario para nao sujar data/state.json
tmpdir = tempfile.mkdtemp()

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from telegram_forwarder.core.forwarder import State

PHONE_EXAMPLE = '+5511999999999'  # numero de exemplo (nunca use numeros reais no codigo)

st = State(path=os.path.join(tmpdir, 'state.json'))

# 1) Estado vazio -> last_id = 0
assert st.get_last_id(PHONE_EXAMPLE, '@canal_origem') == 0, 'estado inicial deveria ser 0'
print('OK 1: estado inicial vazio = 0')

# 2) Salva e recarrega
st.set_last_id(PHONE_EXAMPLE, '@canal_origem', 6343, '@meu_canal')
st2 = State(path=os.path.join(tmpdir, 'state.json'))
v = st2.get_last_id(PHONE_EXAMPLE, '@canal_origem')
assert v == 6343, 'esperado 6343, obtido {}'.format(v)
print('OK 2: persistencia apos recarregar =', v)

# 3) Normalizacao de canal: @User vs @user vs t.me/user devem ser a mesma chave
st2.set_last_id(PHONE_EXAMPLE, '@Canal_Origem', 9999, '')
st3 = State(path=os.path.join(tmpdir, 'state.json'))
assert st3.get_last_id(PHONE_EXAMPLE, '@canal_origem') == 9999, 'normalizacao @ falhou'
assert st3.get_last_id(PHONE_EXAMPLE, 't.me/canal_origem') == 9999, 'normalizacao t.me falhou'
assert st3.get_last_id(PHONE_EXAMPLE, 'https://t.me/canal_origem') == 9999, 'normalizacao https falhou'
print('OK 3: normalizacao de canais (@, t.me, https) consistente')

# 4) Canais diferentes -> estados independentes
assert st3.get_last_id(PHONE_EXAMPLE, '@outro_canal') == 0, 'canal diferente deveria ter estado 0'
assert st3.get_last_id('+5599999999999', '@canal_origem') == 0, 'conta diferente deveria ter estado 0'
print('OK 4: chaves independentes por conta/canal')

# 5) Ids numericos nao sao alterados
st3.set_last_id(PHONE_EXAMPLE, '-1001234567890', 1234, '')
st4 = State(path=os.path.join(tmpdir, 'state.json'))
assert st4.get_last_id(PHONE_EXAMPLE, '-1001234567890') == 1234, 'id numerico falhou'
print('OK 5: ids numericos (-100...) preservados')

print('=== TODOS OS TESTES DE ESTADO PASSARAM ===')
