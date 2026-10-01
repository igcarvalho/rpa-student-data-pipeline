"""Relatório: gera o arquivo Excel final com 3 abas (Resumo, Válidos, Inválidos)."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger("rpa_robot")


def gerar_relatorio(
    df_validos: pd.DataFrame,
    df_invalidos: pd.DataFrame,
    output_dir: str | Path,
    tempo_execucao_segundos: float,
) -> Path:
    """Gera o relatório Excel com as abas Resumo, Válidos e Inválidos.

    Args:
        df_validos: DataFrame com os registros válidos.
        df_invalidos: DataFrame com os registros inválidos (coluna 'erro').
        output_dir: diretório onde o relatório será salvo.
        tempo_execucao_segundos: tempo total de execução do robô.

    Returns:
        Caminho do arquivo gerado.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo com timestamp: relatorio_AAAAMMDD_HHMMSS.xlsx
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = output_path / f"relatorio_{timestamp}.xlsx"

    # --- Aba Resumo ---
    total = len(df_validos) + len(df_invalidos)
    pct_sucesso = (len(df_validos) / total * 100) if total > 0 else 0.0

    resumo = pd.DataFrame(
        [
            {"Métrica": "Total de registros processados", "Valor": total},
            {"Métrica": "Registros válidos", "Valor": len(df_validos)},
            {"Métrica": "Registros inválidos", "Valor": len(df_invalidos)},
            {"Métrica": "Percentual de sucesso", "Valor": f"{pct_sucesso:.1f}%"},
            {"Métrica": "Tempo de execução (segundos)", "Valor": f"{tempo_execucao_segundos:.2f}"},
            {
                "Métrica": "Data/hora do processamento",
                "Valor": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
        ]
    )

    # --- Gravação do Excel com 3 abas ---
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        resumo.to_excel(writer, sheet_name="Resumo", index=False)
        df_validos.to_excel(writer, sheet_name="Validos", index=False)
        df_invalidos.to_excel(writer, sheet_name="Invalidos", index=False)

    logger.info(f"Relatório gerado: {arquivo}")
    return arquivo
