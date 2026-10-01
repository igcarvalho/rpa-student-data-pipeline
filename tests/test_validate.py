"""Testes unitários das regras de validação."""

from __future__ import annotations

import pandas as pd
import pytest

from rpa_students.validate import (
    validar_campos_obrigatorios,
    validar_cpf,
    validar_curso,
    validar_data_ingresso,
    validar_email,
    validar_linha,
)

# ---------------------------------------------------------------------------
# Campos obrigatórios
# ---------------------------------------------------------------------------


def test_campos_obrigatorios_todos_preenchidos():
    linha = {
        "matricula": "2023000001",
        "nome": "Aluno Teste",
        "cpf": "992.459.052-09",
        "email": "aluno@teste.com",
        "curso": "Direito",
        "data_ingresso": "15/03/2023",
    }
    assert validar_campos_obrigatorios(linha) == []


def test_campos_obrigatorios_campo_vazio():
    linha = {
        "matricula": "2023000001",
        "nome": "",
        "cpf": "992.459.052-09",
        "email": "aluno@teste.com",
        "curso": "Direito",
        "data_ingresso": "15/03/2023",
    }
    erros = validar_campos_obrigatorios(linha)
    assert len(erros) == 1
    assert "nome" in erros[0]


def test_campos_obrigatorios_campo_none():
    linha = {
        "matricula": "2023000001",
        "nome": "Aluno Teste",
        "cpf": None,
        "email": "aluno@teste.com",
        "curso": "Direito",
        "data_ingresso": "15/03/2023",
    }
    erros = validar_campos_obrigatorios(linha)
    assert len(erros) == 1
    assert "cpf" in erros[0]


def test_campos_obrigatorios_espacos_vazios():
    linha = {
        "matricula": "2023000001",
        "nome": "Aluno Teste",
        "cpf": "992.459.052-09",
        "email": "   ",
        "curso": "Direito",
        "data_ingresso": "15/03/2023",
    }
    erros = validar_campos_obrigatorios(linha)
    assert len(erros) == 1
    assert "email" in erros[0]


# ---------------------------------------------------------------------------
# CPF
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cpf",
    [
        "992.459.052-09",  # válido com pontuação
        "99245905209",  # válido sem pontuação
        "529.982.247-25",  # outro CPF válido
    ],
)
def test_cpf_valido(cpf):
    assert validar_cpf(cpf) is True


@pytest.mark.parametrize(
    "cpf",
    [
        "111.111.111-11",  # todos os dígitos iguais
        "000.000.000-00",  # todos zeros
        "123.456.789-00",  # dígitos verificadores errados
        "992.459.052-00",  # dígito verificador errado
        "123",  # muito curto
        "abcdefghijk",  # não é número
        "",  # vazio
    ],
)
def test_cpf_invalido(cpf):
    assert validar_cpf(cpf) is False


# ---------------------------------------------------------------------------
# E-mail
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email",
    [
        "aluno@teste.com",
        "aluno.sobrenome@universidade.edu.br",
        "aluno+tag@dominio.com",
        "aluno123@teste.co.uk",
    ],
)
def test_email_valido(email):
    assert validar_email(email) is True


@pytest.mark.parametrize(
    "email",
    [
        "aluno@.com",  # domínio começa com ponto
        "aluno@dominio",  # sem ponto no domínio
        "aluno dominio.com",  # espaço no meio
        "@dominio.com",  # sem parte local
        "aluno@dominio.",  # ponto final sem TLD
        "aluno@",  # sem domínio
        "",  # vazio
    ],
)
def test_email_invalido(email):
    assert validar_email(email) is False


# ---------------------------------------------------------------------------
# Data de ingresso
# ---------------------------------------------------------------------------


def test_data_valida_passado():
    valido, erro = validar_data_ingresso("15/03/2023")
    assert valido is True
    assert erro == ""


def test_data_valida_hoje():
    from datetime import date

    hoje = date.today().strftime("%d/%m/%Y")
    valido, erro = validar_data_ingresso(hoje)
    assert valido is True
    assert erro == ""


def test_data_futura():
    valido, erro = validar_data_ingresso("01/01/2099")
    assert valido is False
    assert "futura" in erro


@pytest.mark.parametrize(
    "data",
    [
        "15/13/2023",  # mês inválido
        "31/02/2023",  # dia inválido para fevereiro
        "2023-03-15",  # formato ISO (errado)
        "15-03-2023",  # separador errado
        "não informada",  # texto
        "",  # vazio
    ],
)
def test_data_formato_invalido(data):
    valido, erro = validar_data_ingresso(data)
    assert valido is False
    assert "formato inválido" in erro


# ---------------------------------------------------------------------------
# Curso
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "curso",
    ["Direito", "Medicina", "Pedagogia", "Ciência da Computação"],
)
def test_curso_permitido(curso):
    assert validar_curso(curso) is True


@pytest.mark.parametrize(
    "curso",
    ["Astronomia", "Veterinária", "Design de Interiores", ""],
)
def test_curso_nao_permitido(curso):
    assert validar_curso(curso) is False


# ---------------------------------------------------------------------------
# Validação completa da linha
# ---------------------------------------------------------------------------


def test_linha_valida():
    linha = {
        "matricula": "2023000001",
        "nome": "Aluno Teste",
        "cpf": "992.459.052-09",
        "email": "aluno@teste.com",
        "curso": "Direito",
        "data_ingresso": "15/03/2023",
    }
    assert validar_linha(linha) == []


def test_linha_multiplos_erros():
    linha = {
        "matricula": "2023000001",
        "nome": "Aluno Teste",
        "cpf": "111.111.111-11",
        "email": "email-invalido",
        "curso": "Astronomia",
        "data_ingresso": "01/01/2099",
    }
    erros = validar_linha(linha)
    # CPF inválido + e-mail inválido + curso inválido + data futura
    assert len(erros) == 4


def test_linha_para_retorna_sem_validar_demais():
    """Se um campo obrigatório está vazio, não valida as demais regras."""
    linha = {
        "matricula": "2023000001",
        "nome": "",
        "cpf": "cpf-totalmente-invalido",
        "email": "email-invalido",
        "curso": "Curso Inexistente",
        "data_ingresso": "data-invalida",
    }
    erros = validar_linha(linha)
    # Deve retornar apenas o erro do campo vazio
    assert len(erros) == 1
    assert "nome" in erros[0]


# ---------------------------------------------------------------------------
# Separação de válidos e inválidos
# ---------------------------------------------------------------------------


def test_validar_dataframe_separa_validos_e_invalidos():
    from rpa_students.validate import validar_dataframe

    df = pd.DataFrame(
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
                "cpf": "111.111.111-11",
                "email": "aluno2@teste.com",
                "curso": "Direito",
                "data_ingresso": "15/03/2023",
            },
            {
                "matricula": "2023000001",  # duplicada
                "nome": "Aluno Tres",
                "cpf": "529.982.247-25",
                "email": "aluno3@teste.com",
                "curso": "Medicina",
                "data_ingresso": "10/02/2022",
            },
        ]
    )

    validos, invalidos = validar_dataframe(df)

    assert len(validos) == 1
    assert len(invalidos) == 2
    assert "erro" in invalidos.columns
    # A duplicada deve ter o erro de matrícula duplicada
    duplicada = invalidos[invalidos["matricula"] == "2023000001"]
    assert len(duplicada) == 1
    assert "duplicada" in duplicada.iloc[0]["erro"]
