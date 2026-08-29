FROM ghcr.io/lncrawl/lightnovel-crawler:latest

ENV TZ=Asia/Jakarta
ENV LNCRAWL_DATA_PATH=/tmp/lncrawl-data
ENV BACKUP_INTERVAL_SECONDS=900

RUN mkdir -p /tmp/lncrawl-data && chmod 777 /tmp/lncrawl-data

COPY start.py /opt/komiz/start.py

ENTRYPOINT ["/app/.venv/bin/python", "/opt/komiz/start.py"]
