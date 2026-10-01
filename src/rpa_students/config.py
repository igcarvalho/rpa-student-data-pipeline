"""Configuração central do robô: variáveis de ambiente e regras de negócio fixas."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega o arquivo .env (se existir) sem sobrescrever variáveis já definidas.
load_dotenv()


def _get_str(key: str, default: str) -> str:
    """Lê uma variável de ambiente string, usando o default se não estiver definida."""
    value = os.getenv(key)
    return value if value is not None and value != "" else default


def _get_int(key: str, default: int) -> int:
    """Lê uma variável de ambiente inteira, usando o default se inválida ou ausente."""
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Configurações imutáveis do robô, lidas uma única vez na inicialização."""

    # PostgreSQL
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Diretórios do fluxo
    input_dir: str
    processed_dir: str
    output_dir: str
    log_dir: str

    @property
    def database_url(self) -> str:
        """Monta a URL de conexão do SQLAlchemy para o PostgreSQL."""
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Lista fixa de cursos permitidos pela universidade.
# Em um cenário real, viria de uma tabela ou arquivo de configuração do sistema.
ALLOWED_COURSES: tuple[str, ...] = (
    "Administração",
    "Ciência da Computação",
    "Direito",
    "Engenharia Civil",
    "Medicina",
    "Pedagogia",
    "Psicologia",
)

# Colunas obrigatórias que toda planilha de entrada deve ter.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "matricula",
    "nome",
    "cpf",
    "email",
    "curso",
    "data_ingresso",
)


def load_settings() -> Settings:
    """Lê as configurações das variáveis de ambiente (ou defaults seguros)."""
    return Settings(
        db_host=_get_str("DB_HOST", "localhost"),
        db_port=_get_int("DB_PORT", 5432),
        db_name=_get_str("DB_NAME", "rpa_students"),
        db_user=_get_str("DB_USER", "rpa_user"),
        db_password=_get_str("DB_PASSWORD", "rpa_password"),
        input_dir=_get_str("INPUT_DIR", "data/input"),
        processed_dir=_get_str("PROCESSED_DIR", "data/processed"),
        output_dir=_get_str("OUTPUT_DIR", "data/output"),
        log_dir=_get_str("LOG_DIR", "logs"),
    )
