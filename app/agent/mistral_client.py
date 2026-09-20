"""Acesso à API da Mistral.

Todo contato com a SDK fica neste arquivo. Se a SDK mudar de novo, só
este módulo precisa ser ajustado.
"""

from app.config import MISTRAL_API_KEY, MISTRAL_MODEL, validar_configuracao


def criar_cliente():
    """Cria o cliente da Mistral, lendo a chave da variável de ambiente."""
    validar_configuracao()

    # A documentação atual tem duas versões da SDK com imports diferentes.
    # Importar aqui dentro também permite testar o agente sem a SDK instalada.
    try:
        from mistralai.client import Mistral  # SDK v2
    except ImportError:
        from mistralai import Mistral  # SDK v1

    return Mistral(api_key=MISTRAL_API_KEY)


def chamar_modelo(cliente, mensagens: list[dict], tools: list[dict]):
    """Uma chamada ao endpoint de chat completions com as tools disponíveis."""
    return cliente.chat.complete(
        model=MISTRAL_MODEL,
        messages=mensagens,
        tools=tools,
        # "auto": o modelo decide se responde ou se usa uma tool.
        tool_choice="auto",
        # Uma tool por vez, em ordem. Sem isso o modelo poderia pedir
        # consultar_disponibilidade e criar_reserva ao mesmo tempo.
        parallel_tool_calls=False,
        # Baixa: queremos respostas consistentes, não criativas.
        temperature=0.2,
    )
