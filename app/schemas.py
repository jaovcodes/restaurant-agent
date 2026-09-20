"""Schemas Pydantic.

Validam os argumentos que o modelo envia para as tools ANTES de executá-las.
O modelo pode errar (esquecer um campo, mandar texto onde deveria ser número).
Com a validação, o erro volta para ele em forma legível e ele pode se corrigir,
em vez de a aplicação quebrar.

(Os schemas de entrada e saída do endpoint /chat entram na Etapa 6.)
"""

from pydantic import BaseModel, ConfigDict


class _ArgumentosBase(BaseModel):
    # extra="forbid": um campo desconhecido gera erro em vez de ser ignorado em silêncio.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConsultarCardapioArgs(_ArgumentosBase):
    categoria: str | None = None
    produto: str | None = None


class ConsultarPrecoArgs(_ArgumentosBase):
    produto: str


class ConsultarHorarioArgs(_ArgumentosBase):
    dia: str | None = None
    horario: str | None = None


class ConsultarDisponibilidadeArgs(_ArgumentosBase):
    data: str
    horario: str
    pessoas: int


class CriarReservaArgs(_ArgumentosBase):
    nome: str
    data: str
    horario: str
    pessoas: int


class ConsultarReservaArgs(_ArgumentosBase):
    reserva_id: int | None = None
    nome_cliente: str | None = None
    data: str | None = None


class CancelarReservaArgs(_ArgumentosBase):
    reserva_id: int | None = None
    nome_cliente: str | None = None
    data: str | None = None
    confirmado: bool = False
