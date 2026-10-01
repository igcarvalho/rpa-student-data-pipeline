"""Carga: grava os registros válidos no PostgreSQL de forma idempotente.

A idempotência é garantida por uma constraint UNIQUE na coluna 'matricula':
rodar o robô duas vezes com o mesmo arquivo não duplica dados — o registro
existente é atualizado (upsert) em vez de inserido novamente.
"""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger("rpa_robot")


class Base(DeclarativeBase):
    """Classe base dos modelos SQLAlchemy (estilo 2.x)."""


class Student(Base):
    """Modelo da tabela students."""

    __tablename__ = "students"

    # Matrícula é a chave natural do aluno (única, não nula).
    matricula: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    curso: Mapped[str] = mapped_column(String(100), nullable=False)
    data_ingresso: Mapped[object] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"Student(matricula={self.matricula!r}, nome={self.nome!r})"


def create_table(engine) -> None:
    """Cria a tabela students se ela ainda não existir."""
    Base.metadata.create_all(engine)


def _parse_data(data_str: str):
    """Converte a data dd/mm/aaaa (string da planilha) para objeto date."""
    from datetime import datetime

    return datetime.strptime(str(data_str).strip(), "%d/%m/%Y").date()


def _build_upsert(engine, registro: dict):
    """Monta o statement de upsert compatível com o dialecto do banco.

    PostgreSQL e SQLite suportam ON CONFLICT DO UPDATE, mas com sintaxes
    ligeiramente diferentes. Esta função abstrai essa diferença.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    if engine.dialect.name == "postgresql":
        stmt = pg_insert(Student).values(**registro)
    else:
        stmt = sqlite_insert(Student).values(**registro)

    return stmt.on_conflict_do_update(
        index_elements=["matricula"],
        set_={
            "nome": stmt.excluded.nome,
            "cpf": stmt.excluded.cpf,
            "email": stmt.excluded.email,
            "curso": stmt.excluded.curso,
            "data_ingresso": stmt.excluded.data_ingresso,
        },
    )


def load_students(df: pd.DataFrame, engine) -> int:
    """Grava os registros válidos no banco com upsert idempotente.

    Usa transação: se qualquer registro falhar, tudo é desfeito (rollback).

    Args:
        df: DataFrame com os registros válidos (colunas da planilha).
        engine: engine do SQLAlchemy conectado ao banco.

    Returns:
        Número de registros gravados (inseridos ou atualizados).

    Raises:
        SQLAlchemyError: se houver falha na conexão ou na transação.
    """
    if df.empty:
        logger.info("Nenhum registro válido para gravar no banco.")
        return 0

    create_table(engine)

    registros_gravados = 0

    # begin() abre uma transação: commit automático se tudo der certo,
    # rollback automático se qualquer operação falhar.
    with engine.begin() as conn:
        for _, row in df.iterrows():
            registro = {
                "matricula": str(row["matricula"]).strip(),
                "nome": str(row["nome"]).strip(),
                "cpf": str(row["cpf"]).strip(),
                "email": str(row["email"]).strip(),
                "curso": str(row["curso"]).strip(),
                "data_ingresso": _parse_data(row["data_ingresso"]),
            }

            stmt = _build_upsert(engine, registro)
            conn.execute(stmt)
            registros_gravados += 1

    logger.info(f"{registros_gravados} registros gravados no banco (upsert idempotente).")
    return registros_gravados


def create_db_engine(database_url: str):
    """Cria e retorna o engine do SQLAlchemy para o banco."""
    return create_engine(database_url, echo=False)
