FROM python:3.11-slim

WORKDIR /srv

# System deps kept minimal — add build-essential etc. here if a
# teammate's module (e.g. an image/audio lib) needs compiling.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=8080
EXPOSE 8080

# Cloud Run sets $PORT; uvicorn must bind to it.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
