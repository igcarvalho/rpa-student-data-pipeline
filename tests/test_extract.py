"""Testes unitários do módulo de extração."""

from __future__ import annotations

import pandas as pd
import pytest

from rpa_students.extract import (
    ExtractionError,
    extract,
    find_input_file,
    read_spreadsheet,
    validate_columns,
)

# ---------------------------------------------------------------------------
# find_input_file
# ---------------------------------------------------------------------------


def test_find_input_file_xlsx(tmp_path):
    arquivo = tmp_path / "matriculas.xlsx"
    arquivo.write_bytes(b"fake content")
    assert find_input_file(tmp_path) == arquivo


def test_find_input_file_csv(tmp_path):
    arquivo = tmp_path / "matriculas.csv"
    arquivo.write_text("matricula,nome\n1,Aluno")
    assert find_input_file(tmp_path) == arquivo


def test_find_input_file_pasta_vazia(tmp_path):
    with pytest.raises(ExtractionError, match="Nenhum arquivo"):
        find_input_file(tmp_path)


def test_find_input_file_pasta_nao_existe(tmp_path):
    with pytest.raises(ExtractionError, match="Pasta de entrada não encontrada"):
        find_input_file(tmp_path / "inexistente")


# ---------------------------------------------------------------------------
# read_spreadsheet
# ---------------------------------------------------------------------------


def test_read_spreadsheet_xlsx(tmp_path):
    df_original = pd.DataFrame({"matricula": ["1"], "nome": ["Aluno"]})
    arquivo = tmp_path / "dados.xlsx"
    df_original.to_excel(arquivo, index=False, engine="openpyxl")

    df_lido = read_spreadsheet(arquivo)
    assert list(df_lido.columns) == ["matricula", "nome"]
    assert df_lido.iloc[0]["matricula"] == "1"


def test_read_spreadsheet_csv(tmp_path):
    arquivo = tmp_path / "dados.csv"
    arquivo.write_text("matricula,nome\n1,Aluno\n2,Aluna", encoding="utf-8")

    df_lido = read_spreadsheet(arquivo)
    assert len(df_lido) == 2
    assert df_lido.iloc[1]["nome"] == "Aluna"


def test_read_spreadsheet_arquivo_vazio(tmp_path):
    arquivo = tmp_path / "vazio.xlsx"
    pd.DataFrame().to_excel(arquivo, index=False, engine="openpyxl")

    with pytest.raises(ExtractionError, match="vazio"):
        read_spreadsheet(arquivo)


def test_read_spreadsheet_arquivo_corrompido(tmp_path):
    arquivo = tmp_path / "corrompido.xlsx"
    arquivo.write_bytes(b"conteudo invalido")

    with pytest.raises(ExtractionError, match="Falha ao ler"):
        read_spreadsheet(arquivo)


# ---------------------------------------------------------------------------
# validate_columns
# ---------------------------------------------------------------------------


def test_validate_columns_todas_presentes():
    df = pd.DataFrame(
        {
            "matricula": ["1"],
            "nome": ["Aluno"],
            "cpf": ["123"],
            "email": ["a@b.com"],
            "curso": ["Direito"],
            "data_ingresso": ["01/01/2023"],
        }
    )
    # Não deve lançar exceção
    validate_columns(df, "teste.xlsx")


def test_validate_columns_coluna_faltando():
    df = pd.DataFrame({"matricula": ["1"], "nome": ["Aluno"]})
    with pytest.raises(ExtractionError, match="colunas obrigatórias"):
        validate_columns(df, "teste.xlsx")


def test_validate_columns_mensagem_lista_colunas_faltando():
    df = pd.DataFrame({"matricula": ["1"], "nome": ["Aluno"]})
    with pytest.raises(ExtractionError) as exc_info:
        validate_columns(df, "teste.xlsx")
    assert "cpf" in str(exc_info.value)
    assert "email" in str(exc_info.value)


# ---------------------------------------------------------------------------
# extract (integração)
# ---------------------------------------------------------------------------


def test_extract_sucesso(tmp_path):
    df_original = pd.DataFrame(
        {
            "matricula": ["1"],
            "nome": ["Aluno"],
            "cpf": ["123"],
            "email": ["a@b.com"],
            "curso": ["Direito"],
            "data_ingresso": ["01/01/2023"],
        }
    )
    df_original.to_excel(tmp_path / "matriculas.xlsx", index=False, engine="openpyxl")

    df = extract(tmp_path)
    assert len(df) == 1
    assert list(df.columns) == list(df_original.columns)


def test_extract_sem_arquivo(tmp_path):
    with pytest.raises(ExtractionError, match="Nenhum arquivo"):
        extract(tmp_path)
