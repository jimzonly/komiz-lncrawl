FROM ghcr.io/lncrawl/lightnovel-crawler:latest

ENV TZ=Asia/Jakarta
ENV LNCRAWL_DATA_PATH=/data
ENV BACKUP_INTERVAL_SECONDS=900

COPY start.py /opt/komiz/start.py

ENTRYPOINT ["/app/.venv/bin/python", "/opt/komiz/start.py"]
