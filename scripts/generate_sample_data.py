"""Gera a planilha de entrada com dados fictícios de matrículas (~200 linhas).

Os dados são 100% inventados (Faker, locale pt_BR) e contêm erros propositais
para exercitar as regras de validação do robô:
  - campos obrigatórios vazios
  - CPFs inválidos
  - e-mails mal formatados
  - matrículas duplicadas
  - datas de ingresso em formato errado ou futuras
  - cursos inexistentes

Uso:
    python scripts/generate_sample_data.py
    python scripts/generate_sample_data.py --output data/input/matriculas.xlsx --rows 200
"""

from __future__ import annotations

import argparse
import random
from datetime import date
from pathlib import Path

import pandas as pd
from faker import Faker

from rpa_students.config import ALLOWED_COURSES

# Gerador de dados fictícios com locale brasileiro.
fake = Faker("pt_BR")

# Colunas da planilha de entrada (mesmas exigidas pelo robô).
COLUMNS = ["matricula", "nome", "cpf", "email", "curso", "data_ingresso"]


def gerar_cpf_valido() -> str:
    """Gera um CPF válido (com dígitos verificadores corretos) no formato 000.000.000-00."""
    # 9 dígitos base aleatórios
    digitos = [random.randint(0, 9) for _ in range(9)]

    # Cálculo do primeiro dígito verificador
    soma1 = sum(d * (10 - i) for i, d in enumerate(digitos))
    digito1 = (soma1 * 10 % 11) % 10
    digitos.append(digito1)

    # Cálculo do segundo dígito verificador
    soma2 = sum(d * (11 - i) for i, d in enumerate(digitos))
    digito2 = (soma2 * 10 % 11) % 10
    digitos.append(digito2)

    cpf = "".join(str(d) for d in digitos)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def gerar_matricula() -> str:
    """Gera uma matrícula no formato AAAANNNNNN (ano + 6 dígitos sequenciais)."""
    ano = random.randint(2019, 2025)
    sequencial = random.randint(0, 999999)
    return f"{ano}{sequencial:06d}"


def gerar_linha_valida() -> dict:
    """Gera uma linha completa e válida (usada como base antes de introduzir erros)."""
    curso = random.choice(ALLOWED_COURSES)
    # Data de ingresso entre 2019 e 2024 (sempre no passado).
    data = fake.date_between(start_date=date(2019, 1, 1), end_date=date(2024, 12, 31))
    return {
        "matricula": gerar_matricula(),
        "nome": fake.name(),
        "cpf": gerar_cpf_valido(),
        "email": fake.free_email(),
        "curso": curso,
        "data_ingresso": data.strftime("%d/%m/%Y"),
    }


def introduzir_erros(df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """Introduz erros propositais em ~25% das linhas para exercitar a validação.

    Cada tipo de erro é aplicado em um subconjunto diferente de linhas,
    garantindo diversidade de casos inválidos.
    """
    rng = random.Random(random_state)
    total = len(df)
    indices = list(range(total))
    rng.shuffle(indices)

    def pegar(n: int) -> list[int]:
        """Pega os próximos n índices da lista embaralhada."""
        return [indices.pop() for _ in range(min(n, len(indices)))]

    # 1. Campos obrigatórios vazios (~10% das linhas)
    for idx in pegar(int(total * 0.10)):
        coluna = rng.choice(["nome", "cpf", "email", "curso", "data_ingresso"])
        df.at[idx, coluna] = ""

    # 2. CPFs inválidos (~8%)
    for idx in pegar(int(total * 0.08)):
        parte1 = rng.randint(100, 999)
        parte2 = rng.randint(100, 999)
        parte3 = rng.randint(100, 999)
        df.at[idx, "cpf"] = f"{parte1}.{parte2}.{parte3}-00"

    # 3. E-mails mal formatados (~8%)
    emails_errados = [
        "aluno@.com",
        "aluno@dominio",
        "aluno dominio.com",
        "@dominio.com",
        "aluno@dominio.",
    ]
    for idx in pegar(int(total * 0.08)):
        df.at[idx, "email"] = rng.choice(emails_errados)

    # 4. Datas em formato errado ou futuras (~8%)
    datas_erradas = ["15/13/2023", "2023-13-45", "01/01/2030", "31/02/2022", "não informada"]
    for idx in pegar(int(total * 0.08)):
        df.at[idx, "data_ingresso"] = rng.choice(datas_erradas)

    # 5. Cursos inexistentes (~6%)
    cursos_errados = ["Astronomia", "Veterinária", "Design de Interiores", "Filosofia"]
    for idx in pegar(int(total * 0.06)):
        df.at[idx, "curso"] = rng.choice(cursos_errados)

    # 6. Matrículas duplicadas (~5%): copia a matrícula de outra linha
    for idx in pegar(int(total * 0.05)):
        outra = rng.choice([i for i in range(total) if i != idx])
        df.at[idx, "matricula"] = df.at[outra, "matricula"]

    return df


def gerar_planilha(rows: int = 200) -> pd.DataFrame:
    """Gera o DataFrame completo com linhas válidas e erros propositais."""
    # Gera linhas válidas (com algumas matrículas repetidas para duplicidade real)
    linhas = [gerar_linha_valida() for _ in range(rows)]
    df = pd.DataFrame(linhas, columns=COLUMNS)

    # Introduz os erros propositais
    df = introduzir_erros(df)

    # Embaralha as linhas para não agrupar os erros no final
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    return df


def main() -> None:
    """Ponto de entrada do script: gera e salva a planilha de entrada."""
    descricao = "Gera planilha de matrículas fictícias com erros."
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument(
        "--output", default="data/input/matriculas.xlsx", help="Caminho do arquivo de saída"
    )
    parser.add_argument("--rows", type=int, default=200, help="Número de linhas a gerar")
    args = parser.parse_args()

    df = gerar_planilha(rows=args.rows)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(output_path, index=False, engine="openpyxl")

    print(f"Planilha gerada: {output_path} ({len(df)} linhas)")


if __name__ == "__main__":
    main()
