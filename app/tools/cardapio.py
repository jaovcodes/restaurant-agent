"""Tools de cardápio: consultar_cardapio e consultar_preco."""

from sqlalchemy.orm import Session

from app.models import Cardapio
from app.tools.utils import ErroTool, normalizar, tratar_erros


def _item_para_dict(item: Cardapio) -> dict:
    return {
        "nome": item.nome,
        "categoria": item.categoria,
        "descricao": item.descricao,
        # Decimal não é serializável em JSON, por isso convertemos para float.
        "preco": float(item.preco),
        "disponivel": item.disponivel,
    }


def _buscar_produtos(db: Session, texto: str) -> list[Cardapio]:
    """Busca produtos por nome, ignorando maiúsculas e acentos.

    Um nome idêntico tem prioridade. Caso contrário, devolve todos os itens
    que contêm todas as palavras digitadas ('risoto' -> 'Risoto de Funghi').
    """
    consulta = normalizar(texto or "")
    if not consulta:
        raise ErroTool("produto_nao_informado", "Informe o nome do produto.")

    itens = db.query(Cardapio).order_by(Cardapio.id).all()

    exatos = [i for i in itens if normalizar(i.nome) == consulta]
    if exatos:
        return exatos

    palavras = consulta.split()
    return [i for i in itens if all(p in normalizar(i.nome) for p in palavras)]


@tratar_erros
def consultar_cardapio(
    db: Session, categoria: str | None = None, produto: str | None = None
) -> dict:
    """Lista o cardápio, filtra por categoria ou detalha um produto.

    Sem argumentos: devolve todos os itens disponíveis.
    Com `produto`: devolve os detalhes (descrição, categoria, preço).
    Com `categoria`: devolve só os itens daquela categoria.
    """
    if produto:
        encontrados = _buscar_produtos(db, produto)
        if not encontrados:
            raise ErroTool(
                "produto_nao_encontrado",
                f"Não encontrei '{produto}' no cardápio.",
            )
        return {"itens": [_item_para_dict(i) for i in encontrados]}

    itens = db.query(Cardapio).filter(Cardapio.disponivel.is_(True)).order_by(Cardapio.id).all()
    categorias = list(dict.fromkeys(i.categoria for i in itens))  # únicas, na ordem

    if categoria:
        alvo = normalizar(categoria)
        itens = [
            i
            for i in itens
            if alvo in normalizar(i.categoria) or normalizar(i.categoria) in alvo
        ]
        if not itens:
            raise ErroTool(
                "categoria_nao_encontrada",
                f"Não encontrei a categoria '{categoria}'.",
                categorias_disponiveis=categorias,
            )

    return {"categorias": categorias, "itens": [_item_para_dict(i) for i in itens]}


@tratar_erros
def consultar_preco(db: Session, produto: str) -> dict:
    """Devolve o preço de um produto, sempre lido do banco."""
    encontrados = _buscar_produtos(db, produto)

    if not encontrados:
        raise ErroTool(
            "produto_nao_encontrado",
            f"Não encontrei '{produto}' no cardápio.",
        )

    if len(encontrados) == 1:
        item = encontrados[0]
        return {
            "produto": item.nome,
            "preco": float(item.preco),
            "disponivel": item.disponivel,
        }

    return {
        "varios_resultados": True,
        "mensagem": "Mais de um item corresponde ao pedido. Pergunte ao cliente qual deseja.",
        "itens": [
            {"nome": i.nome, "preco": float(i.preco), "disponivel": i.disponivel}
            for i in encontrados
        ],
    }
