# Python 3.11 slim ベースイメージ
FROM python:3.11-slim

# 環境変数設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係ファイルをコピーして依存関係をインストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ソースコードをコピー
COPY src/ ./src/

# Cloud Run はポート8080を使用
ENV PORT=8080
EXPOSE 8080

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# uvicorn でアプリケーションを起動
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
