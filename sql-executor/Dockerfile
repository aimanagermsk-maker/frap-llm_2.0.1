FROM python:3.11-slim

WORKDIR /app

# PYTHONDONTWRITEBYTECODE=1 — не создавать .pyc на диске (меньше мусора в образе)
# PYTHONUNBUFFERED=1 — логи Python сразу в stdout/stderr (удобно в docker logs)
# PIP_NO_CACHE_DIR=1 — не кэшировать pip-пакеты (меньше размер образа)
# PIP_DISABLE_PIP_VERSION_CHECK=1 — не проверять обновления pip при установке
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        netcat-openbsd \
        iputils-ping \
        curl \
        dnsutils \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9010"]
