"""Extração: localiza e lê a planilha de entrada (xlsx ou csv) da pasta data/input/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rpa_students.config import REQUIRED_COLUMNS

# Extensões suportadas, na ordem de prioridade.
SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".csv")


class ExtractionError(Exception):
    """Erro de extração: arquivo não encontrado, colunas faltando ou formato inválido."""


def find_input_file(input_dir: str | Path) -> Path:
    """Encontra o primeiro arquivo suportado na pasta de entrada.

    Args:
        input_dir: diretório onde a planilha de entrada deve estar.

    Returns:
        Caminho do arquivo encontrado.

    Raises:
        ExtractionError: se a pasta não existir ou não tiver arquivo suportado.
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ExtractionError(f"Pasta de entrada não encontrada: {input_path}")

    for ext in SUPPORTED_EXTENSIONS:
        arquivos = sorted(input_path.glob(f"*{ext}"))
        if arquivos:
            return arquivos[0]

    raise ExtractionError(
        f"Nenhum arquivo {SUPPORTED_EXTENSIONS} encontrado em {input_path}"
    )


def read_spreadsheet(file_path: Path) -> pd.DataFrame:
    """Lê a planilha de entrada e devolve um DataFrame.

    Args:
        file_path: caminho do arquivo (.xlsx, .xls ou .csv).

    Returns:
        DataFrame com os dados lidos.

    Raises:
        ExtractionError: se o arquivo estiver vazio, corrompido ou em formato inválido.
    """
    try:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(file_path, dtype=str, keep_default_na=False, engine="openpyxl")
    except Exception as exc:
        raise ExtractionError(f"Falha ao ler o arquivo {file_path.name}: {exc}") from exc

    if df.empty:
        raise ExtractionError(f"O arquivo {file_path.name} está vazio (sem linhas de dados).")

    return df


def validate_columns(df: pd.DataFrame, file_name: str) -> None:
    """Verifica se todas as colunas obrigatórias estão presentes no DataFrame.

    Args:
        df: DataFrame lido da planilha.
        file_name: nome do arquivo (usado na mensagem de erro).

    Raises:
        ExtractionError: se faltar alguma coluna obrigatória.
    """
    colunas_presentes = set(df.columns)
    colunas_faltando = [col for col in REQUIRED_COLUMNS if col not in colunas_presentes]
    if colunas_faltando:
        raise ExtractionError(
            f"O arquivo {file_name} está sem as colunas obrigatórias: {colunas_faltando}. "
            f"Colunas encontradas: {list(df.columns)}"
        )


def extract(input_dir: str | Path) -> pd.DataFrame:
    """Orquestra a extração: encontra o arquivo, lê e valida as colunas.

    Args:
        input_dir: diretório onde a planilha de entrada deve estar.

    Returns:
        DataFrame com os dados da planilha (todas as colunas como string).

    Raises:
        ExtractionError: se algo falhar (arquivo, leitura ou colunas).
    """
    file_path = find_input_file(input_dir)
    df = read_spreadsheet(file_path)
    validate_columns(df, file_path.name)
    return df
