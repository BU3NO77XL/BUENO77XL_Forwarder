# -*- coding: utf-8 -*-
"""Testa a logica do par (origem, destino) no estado."""
import sys, os, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from telegram_forwarder.core.forwarder import State

tmp = tempfile.mkdtemp()
st = State(path=os.path.join(tmp, 'state.json'))

# simula o estado legado do usuario (UI8 -> Ui8Hub)
st.set_last_id('+5511999999999', '-1002648982837', 6350, '-1004461422809')

# 1) mesmo par (origem, destino legado) -> herda 6350
v1 = st.get_last_id_pair('+5511999999999', '-1002648982837', '-1004461422809')
# 2) mesma origem, destino NOVO (Teste) -> 0 (historico completo)
v2 = st.get_last_id_pair('+5511999999999', '-1002648982837', '-1003906521395')

print('UI8->Ui8Hub:', v1, '| UI8->Teste:', v2)
assert v1 == 6350, 'esperado 6350, obtido {}'.format(v1)
assert v2 == 0, 'esperado 0, obtido {}'.format(v2)
print('LOGICA DO PAR OK')