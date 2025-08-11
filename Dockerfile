FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY parse_securities.py /app/parse_securities.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Non-root is safer; if you hit host-permissions, run the container with --user $(id -u):$(id -g)
RUN useradd -m appuser
USER appuser

VOLUME ["/input", "/output"]

ENTRYPOINT ["/entrypoint.sh"]