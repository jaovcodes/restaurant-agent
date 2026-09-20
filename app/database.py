"""Conexão com o banco e utilidades de sessão."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM."""


# check_same_thread=False é necessário porque o FastAPI atende
# requisições em threads diferentes e o SQLite, por padrão, proíbe isso.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _ativar_foreign_keys(dbapi_connection, connection_record):
    """O SQLite ignora FOREIGN KEY por padrão; aqui ativamos a checagem."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI: abre uma sessão e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas() -> None:
    """Cria as tabelas que ainda não existem."""
    from app import models  # noqa: F401  (registra os modelos no metadata)

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    criar_tabelas()
    print(f"Banco criado em: {DATABASE_URL}")
