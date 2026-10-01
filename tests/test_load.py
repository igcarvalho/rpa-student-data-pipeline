"""Testes unitários do módulo de carga (usando SQLite em memória).

Escolha do SQLite: os testes rodam sem precisar de um servidor PostgreSQL.
A interface do SQLAlchemy é a mesma — a única diferença é o dialecto do
upsert, que o load.py já abstrai via `_build_upsert`.
"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from rpa_students.load import Student, create_table, load_students


@pytest.fixture
def engine():
    """Cria um banco SQLite em memória para cada teste."""
    eng = create_engine("sqlite:///:memory:")
    create_table(eng)
    yield eng
    eng.dispose()


def _df_exemplo() -> pd.DataFrame:
    """DataFrame de exemplo com 2 registros válidos."""
    return pd.DataFrame(
        [
            {
                "matricula": "2023000001",
                "nome": "Aluno Um",
                "cpf": "992.459.052-09",
                "email": "aluno1@teste.com",
                "curso": "Direito",
                "data_ingresso": "15/03/2023",
            },
            {
                "matricula": "2023000002",
                "nome": "Aluno Dois",
                "cpf": "529.982.247-25",
                "email": "aluno2@teste.com",
                "curso": "Medicina",
                "data_ingresso": "10/02/2022",
            },
        ]
    )


def test_load_students_insere_registros(engine):
    df = _df_exemplo()
    total = load_students(df, engine)

    assert total == 2

    with Session(engine) as session:
        alunos = session.scalars(select(Student)).all()
        assert len(alunos) == 2
        assert alunos[0].matricula == "2023000001"
        assert alunos[0].nome == "Aluno Um"


def test_load_students_dataframe_vazio(engine):
    df = pd.DataFrame(columns=["matricula", "nome", "cpf", "email", "curso", "data_ingresso"])
    total = load_students(df, engine)

    assert total == 0

    with Session(engine) as session:
        alunos = session.scalars(select(Student)).all()
        assert len(alunos) == 0


def test_load_students_idempotente(engine):
    """Rodar o load duas vezes com o mesmo DataFrame não duplica registros."""
    df = _df_exemplo()

    # Primeira execução
    total1 = load_students(df, engine)
    assert total1 == 2

    # Segunda execução com os mesmos dados
    total2 = load_students(df, engine)
    assert total2 == 2

    # O banco deve ter apenas 2 registros (não 4)
    with Session(engine) as session:
        alunos = session.scalars(select(Student)).all()
        assert len(alunos) == 2


def test_load_students_atualiza_registro_existente(engine):
    """Se a matrícula já existe, o registro é atualizado (não duplicado)."""
    df1 = _df_exemplo()
    load_students(df1, engine)

    # Mesma matrícula, dados diferentes
    df2 = pd.DataFrame(
        [
            {
                "matricula": "2023000001",
                "nome": "Aluno Um Atualizado",
                "cpf": "992.459.052-09",
                "email": "aluno1.novo@teste.com",
                "curso": "Direito",
                "data_ingresso": "15/03/2023",
            }
        ]
    )
    load_students(df2, engine)

    with Session(engine) as session:
        alunos = session.scalars(select(Student)).all()
        assert len(alunos) == 2  # não duplicou
        aluno1 = next(a for a in alunos if a.matricula == "2023000001")
        assert aluno1.nome == "Aluno Um Atualizado"
        assert aluno1.email == "aluno1.novo@teste.com"


def test_load_students_parcialmente_novo(engine):
    """Gravar um mix de registros novos e existentes funciona corretamente."""
    df1 = _df_exemplo()
    load_students(df1, engine)

    df2 = pd.DataFrame(
        [
            {
                "matricula": "2023000001",  # existente
                "nome": "Aluno Um",
                "cpf": "992.459.052-09",
                "email": "aluno1@teste.com",
                "curso": "Direito",
                "data_ingresso": "15/03/2023",
            },
            {
                "matricula": "2023000003",  # novo
                "nome": "Aluno Três",
                "cpf": "114.447.777-35",
                "email": "aluno3@teste.com",
                "curso": "Pedagogia",
                "data_ingresso": "05/01/2024",
            },
        ]
    )
    total = load_students(df2, engine)

    assert total == 2

    with Session(engine) as session:
        alunos = session.scalars(select(Student)).all()
        assert len(alunos) == 3  # 2 originais + 1 novo
