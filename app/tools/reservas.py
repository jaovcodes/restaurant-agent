"""Tools de reserva: disponibilidade, criação, consulta e cancelamento."""

from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import DURACAO_RESERVA_MINUTOS
from app.models import (
    DIAS_SEMANA,
    MESA_ATIVA,
    RESERVA_CANCELADA,
    RESERVA_CONFIRMADA,
    Horario,
    Mesa,
    Reserva,
)
from app.tools.horarios import buscar_horario
from app.tools.utils import ErroTool, normalizar, parse_data, parse_horario, tratar_erros

INTERVALO_SUGESTOES_MINUTOS = 30
MAX_SUGESTOES = 3


def _agora() -> datetime:
    """Isolada em uma função para os testes poderem simular a data atual."""
    return datetime.now()


def _minutos(hora: time) -> int:
    return hora.hour * 60 + hora.minute


# ---------------------------------------------------------------------------
# Validações
# ---------------------------------------------------------------------------


def _validar_pessoas(pessoas) -> int:
    try:
        quantidade = int(pessoas)
    except (TypeError, ValueError):
        raise ErroTool("pessoas_invalido", "A quantidade de pessoas deve ser um número inteiro.")
    if quantidade < 1:
        raise ErroTool("pessoas_invalido", "A reserva precisa ser para pelo menos 1 pessoa.")
    return quantidade


def _validar_nome(nome) -> str:
    nome_limpo = " ".join(str(nome or "").split())
    if len(nome_limpo) < 2 or len(nome_limpo) > 100:
        raise ErroTool("nome_invalido", "Informe o nome do cliente para a reserva.")
    return nome_limpo


def _validar_data_horario(data_txt: str, horario_txt: str) -> tuple[date, time]:
    data = parse_data(data_txt)
    horario = parse_horario(horario_txt)
    if datetime.combine(data, horario) <= _agora():
        raise ErroTool("data_no_passado", "Esse dia e horário já passaram.")
    return data, horario


def _validar_capacidade(db: Session, pessoas: int) -> None:
    maior = (
        db.query(func.max(Mesa.capacidade)).filter(Mesa.status == MESA_ATIVA).scalar() or 0
    )
    if pessoas > maior:
        raise ErroTool(
            "grupo_muito_grande",
            f"Não temos mesa para {pessoas} pessoas. A maior comporta {maior}.",
            capacidade_maxima=maior,
        )


def _verificar_expediente(db: Session, data: date, horario: time, pessoas: int) -> Horario:
    """Confirma que o restaurante está aberto no dia e horário pedidos."""
    dia_semana = data.weekday()
    expediente = buscar_horario(db, dia_semana)

    if expediente is None or expediente.fechado:
        raise ErroTool(
            "restaurante_fechado",
            f"O restaurante não abre em {DIAS_SEMANA[dia_semana]}.",
        )

    if not (expediente.hora_abertura <= horario < expediente.hora_fechamento):
        raise ErroTool(
            "fora_do_horario",
            f"Nesse dia o restaurante funciona das "
            f"{expediente.hora_abertura.strftime('%H:%M')} às "
            f"{expediente.hora_fechamento.strftime('%H:%M')}.",
            abertura=expediente.hora_abertura.strftime("%H:%M"),
            fechamento=expediente.hora_fechamento.strftime("%H:%M"),
            horarios_alternativos=_sugerir_horarios(db, data, expediente, horario, pessoas),
        )
    return expediente


# ---------------------------------------------------------------------------
# Lógica de disponibilidade
# ---------------------------------------------------------------------------


def _mesas_livres(db: Session, data: date, horario: time, pessoas: int) -> list[Mesa]:
    """Mesas ativas que comportam o grupo e não conflitam com outra reserva.

    Duas reservas na mesma mesa conflitam se começam com menos de
    DURACAO_RESERVA_MINUTOS de diferença. Reservas canceladas são ignoradas.
    A lista vem ordenada da menor para a maior mesa, para não desperdiçar
    uma mesa grande com um grupo pequeno.
    """
    mesas = (
        db.query(Mesa)
        .filter(Mesa.status == MESA_ATIVA, Mesa.capacidade >= pessoas)
        .order_by(Mesa.capacidade, Mesa.id)
        .all()
    )
    reservas_do_dia = (
        db.query(Reserva)
        .filter(Reserva.data == data, Reserva.status == RESERVA_CONFIRMADA)
        .all()
    )
    ocupadas = {
        r.mesa_id
        for r in reservas_do_dia
        if abs(_minutos(r.horario) - _minutos(horario)) < DURACAO_RESERVA_MINUTOS
    }
    return [m for m in mesas if m.id not in ocupadas]


def _sugerir_horarios(
    db: Session, data: date, expediente: Horario, desejado: time, pessoas: int
) -> list[str]:
    """Até 3 horários livres no mesmo dia, os mais próximos do desejado."""
    agora = _agora()
    abertura = _minutos(expediente.hora_abertura)
    fechamento = _minutos(expediente.hora_fechamento)

    candidatos = []
    for minuto in range(abertura, fechamento, INTERVALO_SUGESTOES_MINUTOS):
        candidato = time(minuto // 60, minuto % 60)
        if candidato == desejado or datetime.combine(data, candidato) <= agora:
            continue
        if _mesas_livres(db, data, candidato, pessoas):
            candidatos.append(candidato)

    candidatos.sort(key=lambda h: (abs(_minutos(h) - _minutos(desejado)), h))
    return [h.strftime("%H:%M") for h in sorted(candidatos[:MAX_SUGESTOES])]


# ---------------------------------------------------------------------------
# Formatação e busca de reservas
# ---------------------------------------------------------------------------


def _reserva_para_dict(reserva: Reserva) -> dict:
    return {
        "reserva_id": reserva.id,
        "nome_cliente": reserva.nome_cliente,
        "data": reserva.data.isoformat(),
        "dia_semana": DIAS_SEMANA[reserva.data.weekday()],
        "horario": reserva.horario.strftime("%H:%M"),
        "quantidade_pessoas": reserva.quantidade_pessoas,
        "mesa": reserva.mesa_id,
        "status": reserva.status,
    }


def _localizar_reservas(
    db: Session,
    reserva_id: int | None,
    nome_cliente: str | None,
    data: str | None,
) -> list[Reserva]:
    """Localiza reservas pelo número ou pelo nome (opcionalmente com a data).

    Busca por número: devolve a reserva, seja qual for a data ou o status.
    Busca por nome: devolve só reservas de hoje em diante.
    """
    if reserva_id is None and not (nome_cliente and nome_cliente.strip()):
        raise ErroTool(
            "dados_insuficientes",
            "Informe o número da reserva ou o nome do cliente.",
        )

    consulta = db.query(Reserva)

    if reserva_id is not None:
        try:
            consulta = consulta.filter(Reserva.id == int(reserva_id))
        except (TypeError, ValueError):
            raise ErroTool("id_invalido", "O número da reserva deve ser um número inteiro.")
        return consulta.all()

    consulta = consulta.filter(Reserva.data >= _agora().date())
    if data:
        consulta = consulta.filter(Reserva.data == parse_data(data))
    reservas = consulta.order_by(Reserva.data, Reserva.horario).all()

    # Compara por palavras inteiras: "Ana" não deve encontrar "Mariana".
    palavras = set(normalizar(nome_cliente).split())
    return [r for r in reservas if palavras <= set(normalizar(r.nome_cliente).split())]


def _buscar_reserva_duplicada(
    db: Session, nome_cliente: str, data: date, horario: time
) -> Reserva | None:
    """Reserva confirmada com o mesmo nome, data e horário, se existir."""
    alvo = normalizar(nome_cliente)
    candidatas = (
        db.query(Reserva)
        .filter(
            Reserva.data == data,
            Reserva.horario == horario,
            Reserva.status == RESERVA_CONFIRMADA,
        )
        .all()
    )
    return next((r for r in candidatas if normalizar(r.nome_cliente) == alvo), None)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tratar_erros
def consultar_disponibilidade(db: Session, data: str, horario: str, pessoas: int) -> dict:
    """Informa se há mesa para a data, horário e quantidade de pessoas.

    Se não houver, sugere horários alternativos no mesmo dia.
    """
    quantidade = _validar_pessoas(pessoas)
    dia, hora = _validar_data_horario(data, horario)
    expediente = _verificar_expediente(db, dia, hora, quantidade)
    _validar_capacidade(db, quantidade)

    livres = _mesas_livres(db, dia, hora, quantidade)
    resposta = {
        "disponivel": bool(livres),
        "data": dia.isoformat(),
        "dia_semana": DIAS_SEMANA[dia.weekday()],
        "horario": hora.strftime("%H:%M"),
        "quantidade_pessoas": quantidade,
    }
    if livres:
        resposta["mesas_disponiveis"] = len(livres)
    else:
        resposta["horarios_alternativos"] = _sugerir_horarios(
            db, dia, expediente, hora, quantidade
        )
    return resposta


@tratar_erros
def criar_reserva(db: Session, nome: str, data: str, horario: str, pessoas: int) -> dict:
    """Cria a reserva depois de verificar a disponibilidade.

    A verificação é refeita aqui dentro: a tool nunca confia que o modelo
    já consultou a disponibilidade antes.
    """
    nome_cliente = _validar_nome(nome)
    quantidade = _validar_pessoas(pessoas)
    dia, hora = _validar_data_horario(data, horario)
    expediente = _verificar_expediente(db, dia, hora, quantidade)
    _validar_capacidade(db, quantidade)

    # Evita duplicar a reserva se o cliente (ou uma nova tentativa após uma
    # falha de rede) pedir a mesma coisa duas vezes. Vem antes da checagem de
    # mesas livres, pois a própria reserva existente ocupa uma mesa.
    duplicada = _buscar_reserva_duplicada(db, nome_cliente, dia, hora)
    if duplicada:
        raise ErroTool(
            "reserva_duplicada",
            "Já existe uma reserva confirmada em nome desse cliente para esse dia e horário.",
            reserva=_reserva_para_dict(duplicada),
        )

    livres = _mesas_livres(db, dia, hora, quantidade)
    if not livres:
        raise ErroTool(
            "horario_indisponivel",
            "Não há mesa disponível para esse dia e horário.",
            horarios_alternativos=_sugerir_horarios(db, dia, expediente, hora, quantidade),
        )

    reserva = Reserva(
        nome_cliente=nome_cliente,
        data=dia,
        horario=hora,
        quantidade_pessoas=quantidade,
        mesa_id=livres[0].id,
        status=RESERVA_CONFIRMADA,
    )
    db.add(reserva)
    try:
        db.commit()
    except IntegrityError:
        # Outra requisição ocupou a mesa entre a verificação e o commit.
        db.rollback()
        raise ErroTool(
            "horario_indisponivel",
            "Esse horário acabou de ser ocupado.",
            horarios_alternativos=_sugerir_horarios(db, dia, expediente, hora, quantidade),
        )

    return {"sucesso": True, "reserva": _reserva_para_dict(reserva)}


@tratar_erros
def consultar_reserva(
    db: Session,
    reserva_id: int | None = None,
    nome_cliente: str | None = None,
    data: str | None = None,
) -> dict:
    """Localiza reservas pelo número ou pelo nome do cliente."""
    reservas = _localizar_reservas(db, reserva_id, nome_cliente, data)
    if not reservas:
        raise ErroTool(
            "reserva_nao_encontrada",
            "Não encontrei nenhuma reserva com esses dados.",
        )
    return {"reservas": [_reserva_para_dict(r) for r in reservas]}


@tratar_erros
def cancelar_reserva(
    db: Session,
    reserva_id: int | None = None,
    nome_cliente: str | None = None,
    data: str | None = None,
    confirmado: bool = False,
) -> dict:
    """Cancela uma reserva, mas só depois da confirmação do cliente.

    Funciona em duas etapas:
      1. confirmado=False: localiza a reserva e devolve os dados para o
         cliente conferir. Nada é alterado no banco.
      2. confirmado=True: cancela de fato e atualiza o status.
    """
    reservas = _localizar_reservas(db, reserva_id, nome_cliente, data)
    if not reservas:
        raise ErroTool(
            "reserva_nao_encontrada",
            "Não encontrei nenhuma reserva com esses dados.",
        )

    ativas = [r for r in reservas if r.status == RESERVA_CONFIRMADA]
    if not ativas:
        raise ErroTool("reserva_ja_cancelada", "Essa reserva já está cancelada.")

    if len(ativas) > 1:
        return {
            "cancelada": False,
            "requer_esclarecimento": True,
            "mensagem": "Há mais de uma reserva. Pergunte ao cliente qual deseja cancelar.",
            "reservas": [_reserva_para_dict(r) for r in ativas],
        }

    reserva = ativas[0]
    if datetime.combine(reserva.data, reserva.horario) <= _agora():
        raise ErroTool("reserva_passada", "Essa reserva já passou e não pode ser cancelada.")

    if not confirmado:
        return {
            "cancelada": False,
            "requer_confirmacao": True,
            "mensagem": "Mostre os dados ao cliente e peça confirmação explícita antes de cancelar.",
            "reserva": _reserva_para_dict(reserva),
        }

    reserva.status = RESERVA_CANCELADA
    db.commit()
    return {"cancelada": True, "reserva": _reserva_para_dict(reserva)}
