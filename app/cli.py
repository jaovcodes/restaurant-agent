"""Chat de terminal para testar o agente (antes de existir a API FastAPI).

Uso:
    python -m app.cli            # conversa normal
    python -m app.cli --debug    # mostra as tools que o modelo chama
"""

import logging
import sys
import uuid

from app.agent.agent import Agente, ErroAgente
from app.database import SessionLocal, criar_tabelas


def main() -> None:
    logging.basicConfig(format="   [%(message)s]")
    if "--debug" in sys.argv:
        logging.getLogger("agente").setLevel(logging.INFO)

    criar_tabelas()

    try:
        agente = Agente()
    except RuntimeError as erro:
        print(erro)
        return

    session_id = uuid.uuid4().hex
    print("Assistente do restaurante. Digite 'sair' para encerrar.\n")

    with SessionLocal() as db:
        while True:
            texto = input("Você: ").strip()
            if texto.lower() in {"sair", "exit", "quit"}:
                break
            if not texto:
                continue
            try:
                print(f"Assistente: {agente.responder(db, session_id, texto)}\n")
            except ErroAgente as erro:
                print(f"Assistente: {erro}\n")


if __name__ == "__main__":
    main()
