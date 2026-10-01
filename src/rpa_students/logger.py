"""Configuração de logs: escreve em arquivo (logs/robot.log) e no console."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Formato padrão: data/hora | nível | mensagem
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(log_dir: str | Path, name: str = "rpa_robot") -> logging.Logger:
    """Cria e configura o logger do robô com saída para arquivo e console.

    Args:
        log_dir: diretório onde o arquivo robot.log será criado.
        name: nome do logger (padrão: "rpa_robot").

    Returns:
        Logger configurado com handlers de arquivo e console.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evita handlers duplicados se a função for chamada mais de uma vez.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Handler de arquivo: guarda o histórico completo da execução.
    file_handler = logging.FileHandler(log_path / "robot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Handler de console: acompanha a execução em tempo real.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
