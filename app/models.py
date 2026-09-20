"""Modelos ORM: cardapio, horarios, mesas e reservas."""

from datetime import date, time

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Status possíveis, definidos como constantes para evitar strings soltas no código.
MESA_ATIVA = "ativa"
MESA_INATIVA = "inativa"

RESERVA_CONFIRMADA = "confirmada"
RESERVA_CANCELADA = "cancelada"

DIAS_SEMANA = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}


class Cardapio(Base):
    __tablename__ = "cardapio"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(String(300), default="")
    # Numeric evita os erros de arredondamento do float em valores monetários.
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    disponivel: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<Cardapio {self.nome} R$ {self.preco}>"


class Horario(Base):
    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 0 = segunda ... 6 = domingo (mesma convenção de date.weekday())
    dia_semana: Mapped[int] = mapped_column(nullable=False, unique=True)
    # Nulo nos dois campos significa que o restaurante fecha nesse dia.
    hora_abertura: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_fechamento: Mapped[time | None] = mapped_column(Time, nullable=True)

    @property
    def fechado(self) -> bool:
        return self.hora_abertura is None or self.hora_fechamento is None

    @property
    def nome_dia(self) -> str:
        return DIAS_SEMANA[self.dia_semana]

    def __repr__(self) -> str:
        return f"<Horario {self.nome_dia}>"


class Mesa(Base):
    __tablename__ = "mesas"

    id: Mapped[int] = mapped_column(primary_key=True)
    capacidade: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=MESA_ATIVA)

    reservas: Mapped[list["Reserva"]] = relationship(back_populates="mesa")

    def __repr__(self) -> str:
        return f"<Mesa {self.id} ({self.capacidade} lugares)>"


class Reserva(Base):
    __tablename__ = "reservas"
    # Impede duas reservas CONFIRMADAS para a mesma mesa, data e horário,
    # mesmo que a verificação na camada de tools falhe (ex.: condição de corrida).
    # O índice é parcial: reservas canceladas não contam, para que a mesa
    # possa ser reservada de novo no mesmo horário.
    __table_args__ = (
        Index(
            "uq_mesa_data_horario_confirmada",
            "mesa_id",
            "data",
            "horario",
            unique=True,
            sqlite_where=text(f"status = '{RESERVA_CONFIRMADA}'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_cliente: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    horario: Mapped[time] = mapped_column(Time, nullable=False)
    quantidade_pessoas: Mapped[int] = mapped_column(nullable=False)
    mesa_id: Mapped[int] = mapped_column(ForeignKey("mesas.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=RESERVA_CONFIRMADA)

    mesa: Mapped["Mesa"] = relationship(back_populates="reservas")

    def __repr__(self) -> str:
        return f"<Reserva {self.id} {self.nome_cliente} {self.data} {self.horario}>"
