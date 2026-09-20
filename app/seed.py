"""Popula o banco com dados fictícios do restaurante.

Uso (na raiz do projeto):
    python -m app.seed            # popula, se o banco estiver vazio
    python -m app.seed --reset    # apaga tudo e popula de novo
"""

import sys
from datetime import time
from decimal import Decimal

from app.database import Base, SessionLocal, criar_tabelas, engine
from app.models import Cardapio, Horario, Mesa

# (nome, categoria, descricao, preco)
CARDAPIO = [
    # Entradas
    ("Bruschetta de Tomate", "Entrada", "Pão italiano tostado com tomate, manjericão fresco e azeite.", "28.90"),
    ("Carpaccio de Carne", "Entrada", "Finas fatias de carne com rúcula, parmesão e molho de mostarda.", "42.00"),
    ("Bolinho de Bacalhau", "Entrada", "Seis unidades de bolinho crocante servidas com molho tártaro.", "38.50"),
    # Pratos principais
    ("Risoto de Funghi", "Prato Principal", "Arroz arbóreo cremoso com mix de cogumelos e parmesão.", "68.90"),
    ("Filé ao Molho Madeira", "Prato Principal", "Filé mignon grelhado com molho madeira, arroz e batata rústica.", "89.90"),
    ("Salmão Grelhado", "Prato Principal", "Filé de salmão com legumes salteados e purê de mandioquinha.", "84.00"),
    ("Fettuccine Alfredo", "Prato Principal", "Massa fresca com molho cremoso de queijo parmesão e manteiga.", "58.00"),
    ("Moqueca de Peixe", "Prato Principal", "Peixe branco cozido no leite de coco e dendê, com arroz e pirão.", "79.90"),
    ("Lasanha à Bolonhesa", "Prato Principal", "Camadas de massa, molho de carne e queijo gratinado.", "54.90"),
    # Sobremesas
    ("Petit Gâteau", "Sobremesa", "Bolinho quente de chocolate com sorvete de creme.", "32.00"),
    ("Pudim de Leite", "Sobremesa", "Pudim tradicional com calda de caramelo.", "18.90"),
    ("Tiramisù", "Sobremesa", "Sobremesa italiana com café, mascarpone e cacau.", "29.90"),
    # Bebidas
    ("Água Mineral", "Bebida", "Garrafa de 500 ml, com ou sem gás.", "6.00"),
    ("Refrigerante Lata", "Bebida", "Lata de 350 ml. Consulte os sabores disponíveis.", "8.00"),
    ("Suco Natural de Laranja", "Bebida", "Copo de 400 ml, feito na hora.", "12.00"),
    ("Limonada Suíça", "Bebida", "Limão batido com leite condensado, copo de 400 ml.", "14.00"),
    ("Cerveja Long Neck", "Bebida", "Garrafa de 330 ml.", "12.90"),
    ("Taça de Vinho Tinto", "Bebida", "Taça de 150 ml da casa.", "24.00"),
    ("Café Expresso", "Bebida", "Dose simples de café expresso.", "7.50"),
]

# (dia_semana, abertura, fechamento) — 0 = segunda ... 6 = domingo
# Horários nulos significam que o restaurante está fechado no dia.
HORARIOS = [
    (0, None, None),                 # segunda: fechado
    (1, time(11, 30), time(23, 0)),  # terça
    (2, time(11, 30), time(23, 0)),  # quarta
    (3, time(11, 30), time(23, 0)),  # quinta
    (4, time(11, 30), time(23, 59)), # sexta
    (5, time(11, 30), time(23, 59)), # sábado
    (6, time(11, 30), time(17, 0)),  # domingo (só almoço)
]

# Capacidades das 10 mesas do salão
CAPACIDADES_MESAS = [2, 2, 2, 2, 4, 4, 4, 4, 6, 8]


def banco_esta_vazio(db) -> bool:
    return db.query(Cardapio).count() == 0 and db.query(Mesa).count() == 0


def popular(db) -> None:
    db.add_all(
        Cardapio(nome=n, categoria=c, descricao=d, preco=Decimal(p), disponivel=True)
        for n, c, d, p in CARDAPIO
    )
    db.add_all(
        Horario(dia_semana=dia, hora_abertura=abre, hora_fechamento=fecha)
        for dia, abre, fecha in HORARIOS
    )
    db.add_all(Mesa(capacidade=cap) for cap in CAPACIDADES_MESAS)
    db.commit()


def main() -> None:
    reset = "--reset" in sys.argv

    if reset:
        Base.metadata.drop_all(bind=engine)
        print("Tabelas apagadas.")

    criar_tabelas()

    with SessionLocal() as db:
        if not banco_esta_vazio(db):
            print("O banco já possui dados. Use --reset para recriar tudo.")
            return
        popular(db)
        print(
            f"Banco populado: {len(CARDAPIO)} itens no cardápio, "
            f"{len(HORARIOS)} horários e {len(CAPACIDADES_MESAS)} mesas."
        )


if __name__ == "__main__":
    main()
