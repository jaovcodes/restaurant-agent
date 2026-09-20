"""Funções auxiliares usadas por todas as tools."""

import functools
import logging
import re
import unicodedata
from datetime import date, time

logger = logging.getLogger(__name__)


class ErroTool(Exception):
    """Erro previsto de regra de negócio (dado inválido, item não encontrado etc.).

    Vira um dicionário {"erro": código, "mensagem": texto} que o modelo
    consegue ler e transformar em uma resposta natural para o cliente.
    """

    def __init__(self, codigo: str, mensagem: str, **extras):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.extras = extras


def tratar_erros(func):
    """Decorator: garante que toda tool devolva um dict, nunca uma exceção.

    - ErroTool (erro previsto)  -> {"erro": ..., "mensagem": ...}
    - qualquer outra exceção    -> erro genérico, sem detalhes técnicos
      (o detalhe vai para o log, não para o usuário).
    """

    @functools.wraps(func)
    def wrapper(db, *args, **kwargs):
        try:
            return func(db, *args, **kwargs)
        except ErroTool as e:
            return {"erro": e.codigo, "mensagem": e.mensagem, **e.extras}
        except Exception:
            db.rollback()
            logger.exception("Erro inesperado na tool %s", func.__name__)
            return {
                "erro": "erro_interno",
                "mensagem": "Não foi possível concluir a operação agora. Tente novamente.",
            }

    return wrapper


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem espaços extras: 'Café  Expresso' -> 'cafe expresso'."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def parse_data(texto: str) -> date:
    """Converte 'AAAA-MM-DD' em date."""
    try:
        return date.fromisoformat(str(texto).strip())
    except ValueError:
        raise ErroTool(
            "data_invalida",
            "A data precisa estar no formato AAAA-MM-DD (por exemplo, 2026-09-25).",
        )


# Aceita "20:00", "20h", "20h30", "8:30", "20:00:00" e "20"
_PADRAO_HORARIO = re.compile(r"^(\d{1,2})(?:h(\d{2})?|:(\d{2})(?::\d{2})?)?$")


def parse_horario(texto: str) -> time:
    """Converte 'HH:MM' (ou variações comuns) em time."""
    correspondencia = _PADRAO_HORARIO.match(str(texto).strip().lower())
    if correspondencia:
        hora = int(correspondencia.group(1))
        minuto = int(correspondencia.group(2) or correspondencia.group(3) or 0)
        if hora <= 23 and minuto <= 59:
            return time(hora, minuto)
    raise ErroTool(
        "horario_invalido",
        "O horário precisa estar no formato HH:MM (por exemplo, 20:00).",
    )
