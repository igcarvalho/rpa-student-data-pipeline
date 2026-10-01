"""Ponto de entrada do robô: orquestra o fluxo completo de processamento.

Fluxo:
    1. Extrai os dados da planilha de entrada (xlsx ou csv)
    2. Valida cada linha e separa válidos de inválidos
    3. Grava os válidos no PostgreSQL (upsert idempotente)
    4. Gera o relatório Excel com 3 abas
    5. Move o arquivo processado para data/processed/ com timestamp

Em caso de falha crítica, o robô registra o erro no log e termina com
código de saída diferente de zero (exit code 1).
"""

from __future__ import annotations

import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from rpa_students.config import load_settings
from rpa_students.extract import ExtractionError, extract, find_input_file
from rpa_students.load import create_db_engine, load_students
from rpa_students.logger import setup_logger
from rpa_students.report import gerar_relatorio
from rpa_students.validate import validar_dataframe

logger = logging.getLogger("rpa_robot")


def mover_arquivo_processado(input_dir: str | Path, processed_dir: str | Path) -> Path:
    """Move o arquivo processado para a pasta de processados com timestamp.

    Args:
        input_dir: diretório onde o arquivo de entrada está.
        processed_dir: diretório de destino.

    Returns:
        Caminho do arquivo movido.
    """
    file_path = find_input_file(input_dir)
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    # Novo nome: matriculas_20261001_131920.xlsx
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    novo_nome = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    destino = processed_path / novo_nome

    shutil.move(str(file_path), str(destino))
    logger.info(f"Arquivo movido para: {destino}")
    return destino


def main() -> int:
    """Executa o fluxo completo do robô.

    Returns:
        0 se a execução foi bem-sucedida, 1 em caso de falha crítica.
    """
    start_time = time.time()

    # --- Setup: configuração e logger ---
    settings = load_settings()
    setup_logger(settings.log_dir)

    logger.info("=" * 60)
    logger.info("Início da execução do robô de processamento de matrículas")
    logger.info("=" * 60)

    try:
        # --- 1. Extração ---
        logger.info(f"Lendo planilha de entrada de: {settings.input_dir}")
        df = extract(settings.input_dir)
        logger.info(f"{len(df)} linhas lidas da planilha.")

        # --- 2. Validação ---
        logger.info("Validando registros...")
        df_validos, df_invalidos = validar_dataframe(df)
        logger.info(
            f"Validação concluída: {len(df_validos)} válidos, {len(df_invalidos)} inválidos."
        )

        # --- 3. Carga no banco ---
        logger.info("Conectando ao banco de dados...")
        engine = create_db_engine(settings.database_url)
        total_gravados = load_students(df_validos, engine)
        logger.info(f"Banco atualizado: {total_gravados} registros gravados.")

        # --- 4. Relatório ---
        tempo_execucao = time.time() - start_time
        logger.info("Gerando relatório Excel...")
        caminho_relatorio = gerar_relatorio(
            df_validos, df_invalidos, settings.output_dir, tempo_execucao
        )

        # --- 5. Mover arquivo processado ---
        mover_arquivo_processado(settings.input_dir, settings.processed_dir)

        # --- Resumo final ---
        logger.info("=" * 60)
        logger.info("Execução concluída com sucesso!")
        logger.info(f"Tempo total: {tempo_execucao:.2f} segundos")
        logger.info(f"Relatório: {caminho_relatorio}")
        logger.info("=" * 60)
        return 0

    except ExtractionError as e:
        # Erros de extração: arquivo não encontrado, colunas faltando, etc.
        logger.error(f"Erro de extração: {e}")
        return 1

    except SQLAlchemyError as e:
        # Erros de banco de dados: conexão falhou, transação falhou, etc.
        logger.error(f"Erro no banco de dados: {e}")
        return 1

    except Exception as e:
        # Erros inesperados: tipo inesperado, erro de sistema, etc.
        logger.error(f"Erro inesperado: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
