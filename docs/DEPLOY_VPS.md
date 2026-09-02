# 🚀 Deploy na VPS (Google Cloud e2-micro) — Modo Daemon

Guia para rodar o forwarder **24/7 na VPS**, encaminhando **apenas as mensagens novas** do canal de origem para o seu canal de destino.

---

## ✅ O que mudou (detecção de mensagens novas)

O sistema agora mantém um **estado persistente** em `data/state.json`:

- Guarda o `id` da **última mensagem já enviada** de cada canal de origem (por conta).
- **Primeira execução** (sem estado): envia o histórico completo.
- **Execuções seguintes**: envia **somente mensagens com id maior** que a última enviada, em ordem cronológica.
- O estado é salvo **após cada envio bem-sucedido** — se o processo cair, ele retoma exatamente de onde parou.
- A GUI (`main.py`) e o daemon (`daemon.py`) **compartilham o mesmo estado**.

> Como você já enviou as 5852 mensagens localmente, basta **copiar a pasta do projeto para a VPS** (incluindo `account/`, `data/` e `.env`) que o daemon continuará de onde a GUI parou, enviando só o que for postado de agora em diante.

---

## 📋 Passo 1 — Preparar os arquivos na sua máquina local

Copie a pasta do projeto para a VPS **com as sessões e o estado**:

```bash
# Na sua máquina (Mac), envie o projeto para a VPS (ajuste usuario e IP):
rsync -av --progress \
  --exclude '.git' --exclude '__pycache__' --exclude 'downloads/*' --exclude 'delete/*' \
  ~/Desktop/Telegram-Restricted-Content-Forwarder \
  usuario@SEU_IP_VPS:/home/usuario/
```

⚠️ **Importante:** as pastas `account/` (sessão `.session`) e `data/` (credenciais + `state.json`) **precisam ir junto** — é nelas que está o progresso do envio. O arquivo `.env` (se você já o criou localmente) também.

---

## 🖥️ Passo 2 — Preparar a VPS (Ubuntu/Debian)

```bash
# Atualizar e instalar Python 3.11 + uv (gerenciador de dependencias)
# PROJETO FIXADO EM PYTHON 3.11 (TgCrypto só tem wheel até 3.11)
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv curl
curl -LsSf https://astral.sh/uv/install.sh | sh   # instala uv
uv python pin 3.11  # garante 3.11 mesmo se sistema tiver 3.12

# Entrar na pasta do projeto
cd ~/Telegram-Restricted-Content-Forwarder

# Instalar dependencias do daemon (sem GUI) via uv
uv sync --extra daemon       # cria .venv e instala apenas o necessario p/ VPS
```

> A e2-micro (0.25–2 vCPU, 1 GB RAM) roda o daemon tranquilamente, pois ele não tem interface gráfica e conecta/desconecta a cada ciclo.

---

## ⚙️ Passo 3 — Configurar o `.env`

```bash
cp .env.example .env
nano .env
```

Preencha:

```ini
API_ID=1234567
API_HASH=a1b2c3...
PHONE=+5511999999999           # EXEMPLO - use o SEU numero real
FROM_CHAT=@canal_origem        # ou -100xxxxxxxxxx
TO_CHAT=-100xxxxxxxxxx         # seu canal
CHECK_INTERVAL=120             # verifica a cada 2 minutos
```

---

## 🎯 Passo 3.0 — IMPORTANTE: marcar o histórico já enviado (só 1 vez)

Como você já enviou as 5852 mensagens **antes** do estado persistente existir, o `data/state.json` ainda não existe. Sem ele, a primeira execução reenviaria **tudo** de novo. Para evitar isso, rode o `tg-seed` (`src/telegram_forwarder/daemon/seed.py`) — ele apenas lê o id da mensagem mais recente do canal e grava no estado, **sem reenviar nada**:

```bash
uv run tg-seed
# compat: uv run python seed_state.py
# ou: uv run python -m telegram_forwarder.daemon.seed
```

Saída esperada:

```
Conectado a +5511999999999...
Estado marcado: ultima mensagem do canal @origem = id=6343
A partir de agora, apenas mensagens NOVAS (id > 6343) serao enviadas.
```

> Alternativa: se preferir, rode a GUI local (`python main.py`) uma vez com o canal — ela agora também grava o estado automaticamente a cada envio. Mas como o histórico já foi enviado, o `seed_state.py` é o caminho direto.

---

## 🧪 Passo 3.1 — Testar manualmente

```bash
uv run tg-daemon
# compat: uv run python daemon.py
# ou: uv run python -m telegram_forwarder.daemon.daemon
```

Você deve ver algo como:

```
[2026-08-28 12:00:00] Daemon iniciado. Conta=+55... Origem=@origem Destino=@destino Intervalo=120s
[2026-08-28 12:00:05] Conectado a +55...
[2026-08-28 12:00:07] Estado encontrado: ultima enviada id=6343 (somente novas serao enviadas).
[2026-08-28 12:00:08] Nenhuma mensagem nova.
```

`Ctrl+C` para parar. Se estiver funcionando, siga para o systemd.

---

## 🔁 Passo 4 — Rodar 24/7 com systemd (reinicia sozinho)

```bash
sudo nano /etc/systemd/system/tgforwarder.service
```

Conteúdo (ajuste `usuario` e o caminho):

```ini
[Unit]
Description=Telegram Restricted Content Forwarder (daemon)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=usuario
WorkingDirectory=/home/usuario/Telegram-Restricted-Content-Forwarder
# src layout + console script (uv cria .venv)
ExecStart=/home/usuario/Telegram-Restricted-Content-Forwarder/.venv/bin/tg-daemon
# alternativas compat:
# ExecStart=/home/usuario/Telegram-Restricted-Content-Forwarder/.venv/bin/python -m telegram_forwarder.daemon.daemon
# ExecStart=/home/usuario/Telegram-Restricted-Content-Forwarder/.venv/bin/python daemon.py
Restart=always
RestartSec=30
# Se a internet cair, o pyrogram pode demorar; timeout evita travar:
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

> **Nota src layout:** o projeto agora usa `src/telegram_forwarder/` (instalado via `uv sync`). O `WorkingDirectory` deve ser a raiz do projeto para que `data/state.json`, `account/` e `.env` sejam encontrados via `core/paths.py` (detecta `pyproject.toml`). `venv/` antigo virou `.venv/`.

Ativar e iniciar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgforwarder   # inicia junto com a VPS (boot)
sudo systemctl start tgforwarder
```

Ver logs em tempo real:

```bash
journalctl -u tgforwarder -f
```

Outros comandos úteis:

```bash
sudo systemctl status tgforwarder    # ver status
sudo systemctl restart tgforwarder   # reiniciar
sudo systemctl stop tgforwarder      # parar
```

---

## 🧠 Como funciona a detecção de novas mensagens

1. A cada `CHECK_INTERVAL` segundos o daemon conecta e lê o histórico **mais recente** do canal de origem.
2. Compara com `data/state.json` (último id enviado).
3. Se houver mensagens com `id > last_id`, envia **apenas essas**, da mais antiga para a mais nova.
4. Atualiza o estado após cada envio (gravação atômica, à prova de queda).

### Comandos úteis de manutenção

```bash
# Ver o estado atual (ultima mensagem enviada por canal)
cat data/state.json

# Forçar reenvio completo do historico (apagar estado)
rm data/state.json && sudo systemctl restart tgforwarder

# Verificar memoria/CPU do daemon na e2-micro
systemd-cgtop
```

---

## 💡 Dicas para a e2-micro (1 GB RAM)

- O daemon é leve (~50–80 MB). Não rode a GUI na VPS — ela é só para desktop.
- `CHECK_INTERVAL=120` é um bom equilíbrio; valores muito baixos aumentam risco de FloodWait.
- Se o canal usar **token de convite** (`t.me/+xxxx`), a conta precisa já ser participante (a GUI local já entrou; a sessão copiada mantém a participação).
- Mantenha a pasta `downloads/` no projeto — os arquivos baixados são apagados após cada envio.

---

## 🔒 Segurança

- **Nunca** commite o `.env`, `account/*.session` ou `data/*.json` (já estão no `.gitignore`).
- Na VPS, restrinja permissões: `chmod 600 .env` e `chmod -R go-rwx account/ data/`.