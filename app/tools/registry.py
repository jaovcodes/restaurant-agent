"""Registro das tools: liga o nome que o modelo escolhe à função Python real.

O modelo devolve um texto (o nome da tool) e um JSON (os argumentos).
Este módulo converte isso em uma chamada de função segura:
    nome -> função + schema Pydantic -> valida -> executa -> dict
"""

import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import schemas
from app.tools.cardapio import consultar_cardapio, consultar_preco
from app.tools.horarios import consultar_horario
from app.tools.reservas import (
    cancelar_reserva,
    consultar_disponibilidade,
    consultar_reserva,
    criar_reserva,
)

# nome da tool -> (função que executa, schema que valida os argumentos)
TOOL_REGISTRY = {
    "consultar_cardapio": (consultar_cardapio, schemas.ConsultarCardapioArgs),
    "consultar_preco": (consultar_preco, schemas.ConsultarPrecoArgs),
    "consultar_horario": (consultar_horario, schemas.ConsultarHorarioArgs),
    "consultar_disponibilidade": (consultar_disponibilidade, schemas.ConsultarDisponibilidadeArgs),
    "criar_reserva": (criar_reserva, schemas.CriarReservaArgs),
    "consultar_reserva": (consultar_reserva, schemas.ConsultarReservaArgs),
    "cancelar_reserva": (cancelar_reserva, schemas.CancelarReservaArgs),
}


def executar_tool(db: Session, nome: str, argumentos: str | dict | None) -> dict:
    """Executa uma tool pedida pelo modelo e devolve sempre um dict.

    Nunca lança exceção: qualquer problema vira {"erro": ..., "mensagem": ...},
    que volta ao modelo para ele explicar (ou corrigir a chamada).
    """
    if nome not in TOOL_REGISTRY:
        return {"erro": "ferramenta_desconhecida", "mensagem": f"A ferramenta '{nome}' não existe."}

    funcao, schema = TOOL_REGISTRY[nome]

    try:
        if isinstance(argumentos, str):
            dados = json.loads(argumentos) if argumentos.strip() else {}
        else:
            dados = argumentos or {}
        args = schema(**dados)
    except ValidationError as e:
        detalhes = "; ".join(
            f"{'.'.join(str(parte) for parte in erro['loc']) or 'argumentos'}: {erro['msg']}"
            for erro in e.errors()
        )
        return {"erro": "argumentos_invalidos", "mensagem": f"Argumentos inválidos para {nome}: {detalhes}"}
    except (ValueError, TypeError):
        return {"erro": "argumentos_invalidos", "mensagem": "Os argumentos não são um JSON válido."}

    return funcao(db, **args.model_dump())
