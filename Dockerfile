FROM python:3.14-slim

LABEL description="HSum Backend API using FastAPI"
LABEL maintainer="KaoKsn <libremaintainer@proton.me>"
LABEL version="0.1.0"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libgobject-2.0-0 \
        libglib2.0-0 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libharfbuzz-subset0 \
        libffi8 \
        libjpeg62-turbo \
        libopenjp2-7 \
        fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --system appuser && \
    useradd --system \
    --gid appuser \
    --create-home \
    --home-dir /home/appuser \
    appuser

# Python configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

COPY --chown=appuser:appuser requirements.txt .

RUN	pip install --no-cache --upgrade pip && \
	pip install --no-cache -r requirements.txt

COPY --chown=appuser:appuser ./app ./app

RUN mkdir -p /app/database && \
	chown -R appuser:appuser /app/database

COPY ./database/init.sql /app/database

USER appuser

EXPOSE 3000

ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "3000"]
