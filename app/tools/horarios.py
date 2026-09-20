"""Tool de horário de funcionamento: consultar_horario."""

from datetime import date

from sqlalchemy.orm import Session

from app.models import DIAS_SEMANA, Horario
from app.tools.utils import ErroTool, normalizar, parse_data, parse_horario, tratar_erros

_DIAS_POR_NOME = {
    "segunda": 0,
    "terca": 1,
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sabado": 5,
    "domingo": 6,
}


def buscar_horario(db: Session, dia_semana: int) -> Horario | None:
    """Expediente de um dia da semana (0 = segunda ... 6 = domingo).

    Também é usada pelas tools de reserva.
    """
    return db.query(Horario).filter(Horario.dia_semana == dia_semana).first()


def _resolver_dia(texto: str) -> tuple[int, date | None]:
    """Aceita 'AAAA-MM-DD' ou o nome do dia ('sexta', 'sábado', 'terça-feira')."""
    nome = normalizar(texto).replace("-feira", "").replace(" feira", "")
    if nome in _DIAS_POR_NOME:
        return _DIAS_POR_NOME[nome], None

    try:
        data = parse_data(texto)
    except ErroTool:
        raise ErroTool(
            "dia_invalido",
            "Não entendi o dia. Use uma data (AAAA-MM-DD) ou o nome do dia da semana.",
        )
    return data.weekday(), data


def _formatar_expediente(expediente: Horario | None, dia_semana: int) -> dict:
    fechado = expediente is None or expediente.fechado
    return {
        "dia": DIAS_SEMANA[dia_semana],
        "funciona_neste_dia": not fechado,
        "abertura": None if fechado else expediente.hora_abertura.strftime("%H:%M"),
        "fechamento": None if fechado else expediente.hora_fechamento.strftime("%H:%M"),
    }


@tratar_erros
def consultar_horario(
    db: Session, dia: str | None = None, horario: str | None = None
) -> dict:
    """Informa o horário de funcionamento.

    - Sem `dia`: devolve a semana inteira.
    - Com `dia`: devolve abertura e fechamento daquele dia.
    - Com `dia` e `horario`: informa também se está aberto naquele horário.
    """
    if not dia:
        if horario:
            raise ErroTool("dia_nao_informado", "Informe o dia para verificar o horário.")
        semana = [_formatar_expediente(buscar_horario(db, d), d) for d in range(7)]
        return {"semana": semana}

    dia_semana, data = _resolver_dia(dia)
    expediente = buscar_horario(db, dia_semana)
    resultado = _formatar_expediente(expediente, dia_semana)
    if data:
        resultado["data"] = data.isoformat()

    if horario:
        hora = parse_horario(horario)
        aberto = (
            resultado["funciona_neste_dia"]
            and expediente.hora_abertura <= hora < expediente.hora_fechamento
        )
        resultado["horario_consultado"] = hora.strftime("%H:%M")
        resultado["aberto_no_horario"] = aberto

    return resultado
