# HSum

A FastAPI backend for a software that summarizes patient health parameters for the consulting doctor.

## Setup

```bash

set -e

git clone https://github.com/KaoKsn/Hsum.git && cd Hsum

python -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt || echo "Failed installing dependencies" && false

uvicorn app.main:app --host 127.0.0.1 --port 3000 --reload

curl http://localhost:3000/health
```

## Containerization Support

```bash
set -e

docker compose up -d

docker images hsum # List image information

curl http://localhost/health
```

I am planning of pushing the container to a registry. If that is the case you can directly pull the image using `docker pull docker.io/kaoksn/hsum:release`

## Technologies

<p align="left">
  <img src="https://cdn.simpleicons.org/sqlite/003B57" alt="SQLite Logo" width="100"/>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://cdn.simpleicons.org/fastapi/009688" alt="FastAPI Logo" width="100"/>
</p>
