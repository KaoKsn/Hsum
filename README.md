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
