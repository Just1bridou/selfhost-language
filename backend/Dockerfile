FROM python:3.11-slim

WORKDIR /app

COPY requirements/ ./requirements/
RUN find requirements -name '*.txt' -exec pip install --no-cache-dir -r {} \;

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
