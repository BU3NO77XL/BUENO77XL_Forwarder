# -*- coding: utf-8 -*-
"""
paths.py — resolução centralizada de caminhos.

Todos os módulos devem importar daqui para não depender do CWD.
Detecta PROJECT_ROOT procurando por pyproject.toml subindo a árvore.
Fallback: 3 níveis acima deste arquivo (src/telegram_forwarder/core -> root).
"""

from pathlib import Path

def _find_project_root() -> Path:
    cur = Path(__file__).resolve()
    for parent in cur.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # fallback — estrutura padrão src/telegram_forwarder/core
    return Path(__file__).resolve().parents[3]

PROJECT_ROOT: Path = _find_project_root()

DATA_DIR: Path = PROJECT_ROOT / "data"
ACCOUNT_DIR: Path = PROJECT_ROOT / "account"
DELETE_DIR: Path = PROJECT_ROOT / "delete"
DOWNLOADS_DIR: Path = PROJECT_ROOT / "downloads"
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
CONFIG_DIR: Path = PROJECT_ROOT / "config"

# Arquivos sensíveis / compatibilidade retroativa
PROXY_FILE: Path = CONFIG_DIR / "proxy.txt"
# fallback legado: se config/proxy.txt não existir, tenta raiz/proxy.txt
if not PROXY_FILE.exists() and (PROJECT_ROOT / "proxy.txt").exists():
    PROXY_FILE = PROJECT_ROOT / "proxy.txt"

ICON_FILE: Path = ASSETS_DIR / "icon.jpg"
if not ICON_FILE.exists() and (PROJECT_ROOT / "icon.jpg").exists():
    ICON_FILE = PROJECT_ROOT / "icon.jpg"

STATE_FILE: Path = DATA_DIR / "state.json"
ENV_FILE: Path = PROJECT_ROOT / ".env"


def ensure_runtime_dirs() -> None:
    """Garante que diretórios de runtime existam (idempotente)."""
    for d in (DATA_DIR, ACCOUNT_DIR, DELETE_DIR, DOWNLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)
