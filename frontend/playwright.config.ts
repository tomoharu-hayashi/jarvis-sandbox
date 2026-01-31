import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  // テストディレクトリ
  testDir: "./e2e",

  // 並列実行
  fullyParallel: true,

  // CIでtest.onlyを禁止
  forbidOnly: !!process.env.CI,

  // CIでのみリトライ
  retries: process.env.CI ? 2 : 0,

  // CIではワーカー数を1に制限
  workers: process.env.CI ? 1 : undefined,

  // レポーター設定
  reporter: [["html", { open: "never" }], ["list"]],

  // 共通設定
  use: {
    baseURL: "http://localhost:3001",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  // ブラウザ設定（Chromiumのみ）
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // テスト実行前にサーバーを起動
  webServer: [
    {
      command: "cd ../smarttodo && uv run uvicorn src.main:app --port 8000",
      url: "http://localhost:8000/api/tasks",
      name: "API Server",
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev -- -p 3001",
      url: "http://localhost:3001",
      name: "Frontend",
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
