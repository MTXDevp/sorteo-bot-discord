FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero (mejor caché de capas).
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --upgrade pip && pip install .

# Datos persistentes (móntalo como volumen en producción).
VOLUME ["/app/data"]

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

CMD ["python", "-m", "sorteo_bot"]
