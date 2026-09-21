"""API HTTP do agente, para a interface web.

Uso:
    uvicorn app.api:app --reload
    # abre em http://127.0.0.1:8000

A lógica do agente NÃO é reimplementada aqui: esta camada só traduz
HTTP para a mesma classe `Agente` que o `cli.py` usa.
"""

import logging
import os
import threading
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.agent import Agente, ErroAgente
from app.database import SessionLocal, criar_tabelas

DIRETORIO_ESTATICO = Path(__file__).parent / "static"


# --------------------------------------------------------------------------
# Captura das tools chamadas, para o painel "ver o que o agente fez".
#
# É a versão web do `--debug` do CLI. O agente já registra cada tool no
# logger "agente"; aqui só guardamos esses registros por thread, porque o
# FastAPI executa cada rota síncrona em uma thread do pool.
# --------------------------------------------------------------------------
class ColetorDeTools(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._por_thread: dict[int, list[str]] = {}

    def emit(self, registro: logging.LogRecord) -> None:
        lista = self._por_thread.get(threading.get_ident())
        if lista is not None:
            lista.append(registro.getMessage())

    def iniciar(self) -> None:
        self._por_thread[threading.get_ident()] = []

    def encerrar(self) -> list[str]:
        return self._por_thread.pop(threading.get_ident(), [])


coletor = ColetorDeTools()
logger_agente = logging.getLogger("agente")
logger_agente.setLevel(logging.INFO)
logger_agente.addHandler(coletor)


# --------------------------------------------------------------------------
# Modelos de entrada e saída
# --------------------------------------------------------------------------
class PedidoChat(BaseModel):
    mensagem: str = Field(min_length=1, max_length=1000)
    session_id: str | None = None


class RespostaChat(BaseModel):
    resposta: str
    session_id: str
    tools: list[str] = []
    erro: bool = False


# --------------------------------------------------------------------------
# Aplicação
# --------------------------------------------------------------------------
app = FastAPI(title="Assistente do restaurante")

# Site do restaurante em outro domínio: liste as origens permitidas no .env,
# separadas por vírgula. Vazio = só a própria página do servidor consegue usar a API.
#   ORIGENS_PERMITIDAS=https://www.saborearte.com.br,https://saborearte.com.br
ORIGENS_PERMITIDAS = [
    origem.strip()
    for origem in os.getenv("ORIGENS_PERMITIDAS", "").split(",")
    if origem.strip()
]
if ORIGENS_PERMITIDAS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_PERMITIDAS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

# O painel "consultas ao sistema" mostra nomes de tools, argumentos e resultados.
# Ótimo para demonstrar e depurar; não deve ficar ligado em um site público.
#   EXIBIR_TOOLS=1
EXIBIR_TOOLS = os.getenv("EXIBIR_TOOLS", "0") == "1"

app.mount("/static", StaticFiles(directory=DIRETORIO_ESTATICO), name="static")

# Uma única instância: a memória das conversas vive dentro dela,
# separada por session_id.
agente = Agente()


@app.on_event("startup")
def preparar_banco() -> None:
    criar_tabelas()


def obter_db():
    with SessionLocal() as db:
        yield db


@app.get("/")
def pagina_inicial() -> FileResponse:
    return FileResponse(DIRETORIO_ESTATICO / "index.html")


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=RespostaChat)
def chat(pedido: PedidoChat, db: Session = Depends(obter_db)) -> RespostaChat:
    session_id = pedido.session_id or uuid.uuid4().hex

    coletor.iniciar()
    try:
        texto = agente.responder(db, session_id, pedido.mensagem.strip())
        erro = False
    except ErroAgente as falha:
        texto = str(falha)
        erro = True
    finally:
        tools = coletor.encerrar()

    return RespostaChat(
        resposta=texto,
        session_id=session_id,
        tools=tools if EXIBIR_TOOLS else [],
        erro=erro,
    )
