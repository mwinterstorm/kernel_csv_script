FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install deps (wheels mean no compiler needed)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY parse_securities.py /app/parse_securities.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Non-root user
RUN useradd -m appuser
USER appuser

# Mount point for your local files
VOLUME ["/data"]

ENTRYPOINT ["/entrypoint.sh"]
