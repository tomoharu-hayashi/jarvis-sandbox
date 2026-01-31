# ============================================================================
# BASE: 共通コマンド（ターゲット名は固定、処理内容はプロジェクトに合わせて変更可）
# ============================================================================
# Makefile (AI開発向け・汎用・薄いルーター)
# 方針: Makefileは「入口」だけ。重い実体は scripts/ に逃がす。
# スクリプト配置:
#   - scripts/base/  : テンプレートリポジトリから提供（pr-review, pr-checks-wait等）
#   - scripts/       : プロジェクト固有（この下に追加）

SHELL := /bin/bash
.DEFAULT_GOAL := help

SCRIPTS_DIR ?= scripts
PR ?= $(shell gh pr view --json number --jq .number 2>/dev/null)

.PHONY: help
help: ## コマンド一覧
	@awk 'BEGIN{FS=":.*##"} /^[a-zA-Z0-9_%-]+:.*##/{printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: doctor
doctor: ## 開発に必要なコマンド/環境のざっくりチェック
	@command -v git >/dev/null || (echo "missing: git" && exit 1)
	@echo "ok: basic"

.PHONY: deps
deps: ## 依存導入
	@cd smarttodo && uv sync --all-extras

.PHONY: run
run: ## 開発サーバー起動
	@cd smarttodo && uv run uvicorn src.main:app --reload

.PHONY: env-local
env-local: ## dotenvxで.env.local + .env を読み込んでコマンド実行（local優先）
	@bash scripts/bws_run.sh local -- $(CMD)

.PHONY: env-prod
env-prod: ## dotenvxで.env.prod + .env を読み込んでコマンド実行（prod優先）
	@bash scripts/bws_run.sh prod -- $(CMD)

.PHONY: env-global
env-global: ## bws globalプロジェクトの値を環境変数として注入してコマンド実行
	@bash scripts/base/bws_global_run.sh -- $(CMD)

.PHONY: test
test: ## テスト実行
	@cd smarttodo && uv run pytest tests/ -v

.PHONY: fmt
fmt: ## フォーマット
	@cd smarttodo && uv run ruff format .

.PHONY: lint
lint: ## リント/静的解析
	@cd smarttodo && uv run ruff check . && uv run ruff format --check .

.PHONY: clean
clean: ## 生成物削除
	@rm -rf .tmp .cache dist build coverage 2>/dev/null || true
	@find . -path "./.git" -prune -o -name ".DS_Store" -type f -delete
	@find . -path "./.git" -prune -o -type d -empty -delete

.PHONY: pr-review
pr-review: ## PRのレビュー/コメントを全取得
	@bash "scripts/base/pr_review.sh"

.PHONY: pr-checks-wait
pr-checks-wait: ## PRのCIチェックをポーリング（TIMEOUT秒で打ち切り、デフォルト: 1800）
	@bash "scripts/base/pr_checks_wait.sh"

.PHONY: pr-merge
pr-merge: ## PRを即時マージ
	@test -n "$(PR)" || (echo "PR not found. Set PR=<number> or checkout a PR branch." && exit 1)
	@gh pr merge "$(PR)" --squash

# ============================================================================
# BASE: ここまで
# ============================================================================

# ============================================================================
# LOCAL: プロジェクト固有コマンド（自由に追加・変更可）
# ============================================================================
# Example:
# .PHONY: install-api-client
# install-api-client: ## APIクライアント導入
# 	@echo "Not defined (Makefile)"
#
# .PHONY: build
# build: ## ビルド
# 	@echo "Not defined (Makefile)"
#
# コマンドが10行以上の場合 scripts/ に逃がす:
# .PHONY: deploy
# deploy: ## デプロイ
# 	@bash scripts/deploy.sh
