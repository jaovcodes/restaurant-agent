"""Núcleo do agente: o loop de function calling com a Mistral.

    Usuário -> Mistral -> (tool_calls?) -> executa tool -> Mistral -> ... -> texto final
"""

import json
import logging

from sqlalchemy.orm import Session

from app.agent.memory import MemoriaSessoes
from app.agent.mistral_client import chamar_modelo, criar_cliente
from app.agent.prompts import montar_system_prompt
from app.config import MAX_ITERACOES_AGENTE
from app.tools.definitions import TOOLS
from app.tools.registry import executar_tool

logger = logging.getLogger("agente")

MSG_INDISPONIVEL = (
    "Desculpe, estou com um problema técnico no momento. "
    "Pode tentar novamente em instantes?"
)
MSG_NAO_CONCLUIDO = "Desculpe, não consegui concluir sua solicitação. Pode reformular o pedido?"


class ErroAgente(Exception):
    """Falha ao gerar a resposta. A mensagem já é adequada para mostrar ao usuário."""


def _extrair_texto(conteudo) -> str:
    """O conteúdo normalmente é str, mas a SDK também pode devolver uma lista de blocos."""
    if conteudo is None:
        return ""
    if isinstance(conteudo, str):
        return conteudo
    partes = []
    for bloco in conteudo:
        texto = bloco.get("text") if isinstance(bloco, dict) else getattr(bloco, "text", None)
        if texto:
            partes.append(texto)
    return "".join(partes)


def _argumentos_como_texto(argumentos) -> str:
    return argumentos if isinstance(argumentos, str) else json.dumps(argumentos, ensure_ascii=False)


def _mensagem_do_assistente(mensagem, chamadas) -> dict:
    """Converte a resposta do modelo (objeto da SDK) em um dict simples.

    Guardar o histórico só com dicts deixa a memória independente da SDK
    e fácil de podar, testar e inspecionar.
    """
    return {
        "role": "assistant",
        "content": _extrair_texto(mensagem.content),
        "tool_calls": [
            {
                "id": chamada.id,
                "type": "function",
                "function": {
                    "name": chamada.function.name,
                    "arguments": _argumentos_como_texto(chamada.function.arguments),
                },
            }
            for chamada in chamadas
        ],
    }


class Agente:
    def __init__(self, cliente=None, memoria: MemoriaSessoes | None = None):
        # `cliente` pode ser injetado: nos testes usamos um cliente falso,
        # sem gastar a API de verdade.
        self.cliente = cliente or criar_cliente()
        self.memoria = memoria or MemoriaSessoes()

    def responder(self, db: Session, session_id: str, texto_usuario: str) -> str:
        """Processa uma mensagem do usuário e devolve a resposta em texto."""
        historico = self.memoria.obter(session_id)
        system = {"role": "system", "content": montar_system_prompt()}

        # Mensagens deste turno. Só vão para a memória se o turno terminar bem,
        # para nunca ficar um histórico quebrado (tool_call sem resposta).
        novas = [{"role": "user", "content": texto_usuario}]

        for _ in range(MAX_ITERACOES_AGENTE):
            try:
                resposta = chamar_modelo(self.cliente, [system] + historico + novas, TOOLS)
            except Exception:
                logger.exception("Falha ao chamar a API da Mistral")
                raise ErroAgente(MSG_INDISPONIVEL)

            mensagem = resposta.choices[0].message
            chamadas = mensagem.tool_calls or []

            # Sem tool_calls: o modelo terminou e esta é a resposta final.
            if not chamadas:
                texto = _extrair_texto(mensagem.content).strip() or MSG_NAO_CONCLUIDO
                novas.append({"role": "assistant", "content": texto})
                self.memoria.adicionar(session_id, novas)
                return texto

            # Com tool_calls: executamos cada uma e devolvemos o resultado ao modelo.
            novas.append(_mensagem_do_assistente(mensagem, chamadas))
            for chamada in chamadas:
                novas.append(self._executar_tool(db, chamada))

        logger.warning("Limite de %s iterações atingido sem resposta final", MAX_ITERACOES_AGENTE)
        raise ErroAgente(MSG_NAO_CONCLUIDO)

    def _executar_tool(self, db: Session, chamada) -> dict:
        nome = chamada.function.name
        argumentos = chamada.function.arguments
        resultado = executar_tool(db, nome, argumentos)
        logger.info("tool %s(%s) -> %s", nome, _argumentos_como_texto(argumentos), resultado)
        return {
            "role": "tool",
            "name": nome,
            "content": json.dumps(resultado, ensure_ascii=False),
            # O id amarra este resultado à chamada que o originou.
            "tool_call_id": chamada.id,
        }
