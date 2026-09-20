"""Definição das tools no formato JSON Schema que a API da Mistral espera.

O modelo NÃO executa nada: ele lê estas descrições para decidir qual tool
chamar e com quais argumentos. Por isso as descrições são escritas para o
modelo, dizendo quando usar (e quando não usar) cada ferramenta.
"""


def _ferramenta(nome: str, descricao: str, propriedades: dict, obrigatorios: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": nome,
            "description": descricao,
            "parameters": {
                "type": "object",
                "properties": propriedades,
                "required": obrigatorios or [],
            },
        },
    }


_DATA = {"type": "string", "description": "Data no formato AAAA-MM-DD."}
_HORARIO = {"type": "string", "description": "Horário no formato HH:MM, 24 horas (ex.: 20:00)."}
_PESSOAS = {"type": "integer", "minimum": 1, "description": "Quantidade de pessoas."}
_RESERVA_ID = {"type": "integer", "description": "Número da reserva, se o cliente souber."}
_NOME_CLIENTE = {"type": "string", "description": "Nome do cliente que fez a reserva."}

TOOLS = [
    _ferramenta(
        "consultar_cardapio",
        "Lista os itens do cardápio ou mostra os detalhes (descrição, categoria e preço) de um "
        "produto. Sem parâmetros, lista tudo o que está disponível. Use para perguntas sobre "
        "pratos, bebidas, sobremesas e categorias.",
        {
            "categoria": {
                "type": "string",
                "description": "Filtra por categoria (ex.: Entrada, Prato Principal, Sobremesa, Bebida).",
            },
            "produto": {
                "type": "string",
                "description": "Nome (ou parte do nome) de um produto para ver seus detalhes.",
            },
        },
    ),
    _ferramenta(
        "consultar_preco",
        "Informa o preço de um produto do cardápio. Use SEMPRE antes de citar qualquer valor.",
        {"produto": {"type": "string", "description": "Nome (ou parte do nome) do produto."}},
        ["produto"],
    ),
    _ferramenta(
        "consultar_horario",
        "Informa o horário de funcionamento do restaurante e se ele está aberto em determinado "
        "dia e horário. Sem parâmetros, devolve a semana inteira.",
        {
            "dia": {
                "type": "string",
                "description": "Data (AAAA-MM-DD) ou nome do dia da semana (segunda, terça, ..., domingo).",
            },
            "horario": {
                "type": "string",
                "description": "Horário HH:MM para verificar se está aberto. Exige o parâmetro dia.",
            },
        },
    ),
    _ferramenta(
        "consultar_disponibilidade",
        "Verifica se há mesa livre para uma data, horário e quantidade de pessoas. Se não houver, "
        "devolve horários alternativos no mesmo dia. NÃO cria reserva.",
        {"data": _DATA, "horario": _HORARIO, "pessoas": _PESSOAS},
        ["data", "horario", "pessoas"],
    ),
    _ferramenta(
        "criar_reserva",
        "Cria uma reserva. Só chame depois que consultar_disponibilidade indicar disponibilidade "
        "e o cliente tiver informado o nome. Confirme a reserva ao cliente somente se esta "
        "ferramenta retornar sucesso.",
        {
            "nome": {"type": "string", "description": "Nome do cliente."},
            "data": _DATA,
            "horario": _HORARIO,
            "pessoas": _PESSOAS,
        },
        ["nome", "data", "horario", "pessoas"],
    ),
    _ferramenta(
        "consultar_reserva",
        "Localiza reservas existentes pelo número da reserva ou pelo nome do cliente (com a data, "
        "opcionalmente). Informa data, horário, quantidade de pessoas e status.",
        {"reserva_id": _RESERVA_ID, "nome_cliente": _NOME_CLIENTE, "data": _DATA},
    ),
    _ferramenta(
        "cancelar_reserva",
        "Cancela uma reserva em DUAS etapas. Etapa 1: chame com confirmado=false; a ferramenta "
        "localiza a reserva e devolve os dados, sem cancelar nada. Mostre os dados ao cliente e "
        "peça confirmação. Etapa 2: somente depois que o cliente responder explicitamente que "
        "confirma o cancelamento, chame novamente com confirmado=true.",
        {
            "reserva_id": _RESERVA_ID,
            "nome_cliente": _NOME_CLIENTE,
            "data": _DATA,
            "confirmado": {
                "type": "boolean",
                "description": "true apenas se o cliente confirmou explicitamente o cancelamento.",
            },
        },
    ),
]
