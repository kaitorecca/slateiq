FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8080
WORKDIR /app
RUN pip install --no-cache-dir "fastapi==0.118.*" "uvicorn[standard]==0.38.*"
COPY main.py /app/main.py
EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
