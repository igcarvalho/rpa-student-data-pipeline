"""Validação: aplica regras de negócio em cada linha e separa válidos de inválidos.

Cada regra é uma função pequena, isolada e testável. A função `validar_linha`
consolida todas as regras e devolve a lista de motivos de erro (vazia = válida).
"""

from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd

from rpa_students.config import ALLOWED_COURSES, REQUIRED_COLUMNS

# Regex simples para e-mail: algo@algo.algo (sem espaços, com ponto no domínio).
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validar_campos_obrigatorios(linha: dict) -> list[str]:
    """Verifica se todos os campos obrigatórios estão preenchidos.

    Args:
        linha: dicionário com os dados de uma linha da planilha.

    Returns:
        Lista de mensagens de erro (vazia se todos os campos estão preenchidos).
    """
    erros = []
    for campo in REQUIRED_COLUMNS:
        valor = linha.get(campo)
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            erros.append(f"Campo obrigatório '{campo}' está vazio.")
    return erros


def validar_cpf(cpf: str) -> bool:
    """Valida um CPF usando o algoritmo dos dígitos verificadores.

    Aceita formatos "000.000.000-00" ou "00000000000". CPFs com todos os
    dígitos iguais (ex: 111.111.111-11) são considerados inválidos.

    Args:
        cpf: string com o CPF (pontos e traço são ignorados).

    Returns:
        True se o CPF é válido, False caso contrário.
    """
    # Remove pontos, traços e espaços
    cpf_limpo = re.sub(r"[.\- ]", "", str(cpf))

    # Precisa ter exatamente 11 dígitos
    if not re.fullmatch(r"\d{11}", cpf_limpo):
        return False

    # Rejeita CPFs com todos os dígitos iguais (ex: 000.000.000-00)
    if len(set(cpf_limpo)) == 1:
        return False

    # Cálculo do primeiro dígito verificador
    soma1 = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    digito1 = (soma1 * 10 % 11) % 10

    # Cálculo do segundo dígito verificador
    soma2 = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    digito2 = (soma2 * 10 % 11) % 10

    return cpf_limpo[9] == str(digito1) and cpf_limpo[10] == str(digito2)


def validar_email(email: str) -> bool:
    """Valida o formato do e-mail usando regex.

    Args:
        email: string com o e-mail a validar.

    Returns:
        True se o formato é válido, False caso contrário.
    """
    return bool(EMAIL_REGEX.match(str(email).strip()))


def validar_data_ingresso(data_str: str) -> tuple[bool, str]:
    """Valida a data de ingresso: formato dd/mm/aaaa, data real e não futura.

    Args:
        data_str: string com a data no formato dd/mm/aaaa.

    Returns:
        Tupla (é_válida, mensagem_de_erro). Se é_válida=True, mensagem é "".
    """
    try:
        data = datetime.strptime(str(data_str).strip(), "%d/%m/%Y").date()
    except ValueError:
        return False, f"Data de ingresso '{data_str}' está em formato inválido (use dd/mm/aaaa)."

    if data > date.today():
        return False, f"Data de ingresso '{data_str}' é futura."

    return True, ""


def validar_curso(curso: str) -> bool:
    """Verifica se o curso está na lista de cursos permitidos.

    Args:
        curso: nome do curso a validar.

    Returns:
        True se o curso é permitido, False caso contrário.
    """
    return str(curso).strip() in ALLOWED_COURSES


def validar_linha(linha: dict) -> list[str]:
    """Aplica todas as regras de validação em uma linha.

    Args:
        linha: dicionário com os dados de uma linha da planilha.

    Returns:
        Lista de motivos de erro (vazia se a linha é válida).
    """
    erros: list[str] = []

    # 1. Campos obrigatórios
    erros.extend(validar_campos_obrigatorios(linha))

    # Se algum campo obrigatório está vazio, as demais regras não se aplicam
    if erros:
        return erros

    # 2. CPF válido
    if not validar_cpf(linha["cpf"]):
        erros.append(f"CPF '{linha['cpf']}' é inválido.")

    # 3. E-mail válido
    if not validar_email(linha["email"]):
        erros.append(f"E-mail '{linha['email']}' tem formato inválido.")

    # 4. Data de ingresso válida e não futura
    data_ok, data_erro = validar_data_ingresso(linha["data_ingresso"])
    if not data_ok:
        erros.append(data_erro)

    # 5. Curso permitido
    if not validar_curso(linha["curso"]):
        erros.append(f"Curso '{linha['curso']}' não é permitido.")

    return erros


def validar_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida todas as linhas do DataFrame e separa válidos de inválidos.

    Também detecta matrículas duplicadas dentro do arquivo: a primeira
    ocorrência é válida e as demais recebem o erro de duplicidade.

    Args:
        df: DataFrame com os dados lidos da planilha.

    Returns:
        Tupla (validos, invalidos): dois DataFrames. O de inválidos tem a
        coluna extra 'erro' com os motivos separados por "; ".
    """
    validos: list[dict] = []
    invalidos: list[dict] = []
    matriculas_vistas: set[str] = set()

    for _, row in df.iterrows():
        linha = row.to_dict()
        erros = validar_linha(linha)

        # 6. Matrícula única dentro do arquivo
        matricula = str(linha["matricula"]).strip()
        if matricula in matriculas_vistas:
            erros.append(f"Matrícula '{matricula}' está duplicada no arquivo.")
        else:
            matriculas_vistas.add(matricula)

        if erros:
            linha["erro"] = "; ".join(erros)
            invalidos.append(linha)
        else:
            validos.append(linha)

    df_validos = pd.DataFrame(validos, columns=list(df.columns))
    df_invalidos = pd.DataFrame(invalidos, columns=list(df.columns) + ["erro"])

    return df_validos, df_invalidos
