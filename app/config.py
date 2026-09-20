"""Configurações da aplicação, lidas de variáveis de ambiente."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Raiz do projeto (pasta que contém "app/")
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Banco de dados ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'restaurante.db'}")

# --- Mistral ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest") 

# --- Regras de negócio ---
# Tempo que uma mesa fica ocupada por uma reserva.
# Usado na Etapa 4 para detectar conflitos de horário.
DURACAO_RESERVA_MINUTOS = int(os.getenv("DURACAO_RESERVA_MINUTOS", "90"))

# Limite de voltas no loop de function calling, para evitar loop infinito.
MAX_ITERACOES_AGENTE = int(os.getenv("MAX_ITERACOES_AGENTE", "5"))


def validar_configuracao() -> None:
    """Falha cedo se a chave da API não estiver definida.

    Chamado no startup da aplicação (Etapa 6), e não no import,
    para que os testes das tools rodem sem precisar de chave.
    """
    if not MISTRAL_API_KEY:
        raise RuntimeError(
            "MISTRAL_API_KEY não definida. "
            "Copie .env.example para .env e preencha sua chave."
        )
