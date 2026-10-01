FROM python:3.12-slim

# Dependências de sistema: psycopg precisa de libpq e gcc para compilar.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia as dependências primeiro para aproveitar o cache do Docker.
COPY pyproject.toml README.md ./
COPY src ./src

# Instala as dependências do projeto.
RUN pip install --no-cache-dir .

# Diretórios de dados (montados como volumes no docker-compose).
RUN mkdir -p data/input data/processed data/output logs

# Comando padrão: executa o robô.
CMD ["python", "-m", "rpa_students.main"]
