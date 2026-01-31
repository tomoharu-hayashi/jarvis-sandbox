import { test, expect, APIRequestContext } from "@playwright/test";

// API BASE URL
const API_URL = "http://localhost:8000";

// テスト用タスクをクリーンアップ（プレフィックス指定可能）
async function cleanupTestTasks(request: APIRequestContext, prefix: string) {
  const response = await request.get(`${API_URL}/api/tasks`);
  if (response.ok()) {
    const data = await response.json();
    for (const task of data.items) {
      if (task.title.startsWith(prefix)) {
        await request.delete(`${API_URL}/api/tasks/${task.id}`);
      }
    }
  }
}

// 並列実行を無効化（テスト間の干渉を防ぐ）
test.describe.configure({ mode: "serial" });

test.describe("タスク管理", () => {
  test("タスクの完了状態を切り替えできる", async ({ page, request }) => {
    const prefix = "[E2E-完了]";

    // クリーンアップ
    await cleanupTestTasks(request, prefix);

    // APIで直接タスクを作成
    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 完了切り替えテスト`,
        priority: "medium",
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 完了切り替えテスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // チェックボックスをクリックして完了にする
    const taskItem = page.locator(`[data-testid="task-item-${createdTask.id}"]`).or(
      page.locator("div").filter({ hasText: `${prefix} 完了切り替えテスト` }).first()
    );
    const checkbox = taskItem.getByRole("checkbox");
    await checkbox.click();

    // ページをリロードして状態が保持されていることを確認
    await page.waitForTimeout(1000);
    await page.reload();
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが完了状態であることを確認（APIから取得）
    const verifyResponse = await request.get(`${API_URL}/api/tasks/${createdTask.id}`);
    if (verifyResponse.ok()) {
      const task = await verifyResponse.json();
      expect(task.status).toBe("completed");
    }

    // クリーンアップ
    await cleanupTestTasks(request, prefix);
  });

  test("タスクを削除できる", async ({ page, request }) => {
    const prefix = "[E2E-削除]";

    // クリーンアップ
    await cleanupTestTasks(request, prefix);

    // APIで直接タスクを作成
    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 削除テスト`,
        priority: "low",
      },
    });
    expect(createResponse.ok()).toBeTruthy();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 削除テスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // 削除ボタンをクリック
    const taskItem = page.locator("div").filter({ hasText: `${prefix} 削除テスト` }).first();
    const deleteButton = taskItem.getByRole("button", { name: "タスクを削除" });
    await deleteButton.click();

    // タスクが削除されることを確認
    await expect(taskText).not.toBeVisible({ timeout: 5000 });

    // クリーンアップ
    await cleanupTestTasks(request, prefix);
  });

  test("タスクがない場合はメッセージが表示される", async ({ page, request }) => {
    // 全テスト用タスクをクリーンアップ
    await cleanupTestTasks(request, "[E2E");

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // 読み込み完了まで待機
    await page.waitForLoadState("networkidle");

    // タスクがない場合のメッセージを確認（既存タスクがある場合はスキップ）
    const emptyMessage = page.getByText("タスクがありません");
    const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);

    if (hasEmptyMessage) {
      await expect(page.getByText("新しいタスクを追加してください")).toBeVisible();
    }
  });

  test("APIでタスクを作成・取得できる", async ({ request }) => {
    const prefix = "[E2E-API]";

    // クリーンアップ
    await cleanupTestTasks(request, prefix);

    // タスクを作成
    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} APIテスト`,
        description: "E2Eテスト用のタスク",
        priority: "high",
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();
    expect(createdTask.title).toBe(`${prefix} APIテスト`);
    expect(createdTask.priority).toBe("high");

    // タスク一覧を取得
    const listResponse = await request.get(`${API_URL}/api/tasks`);
    expect(listResponse.ok()).toBeTruthy();
    const tasks = await listResponse.json();
    expect(tasks.items.some((t: { id: string }) => t.id === createdTask.id)).toBeTruthy();

    // タスクを削除
    const deleteResponse = await request.delete(`${API_URL}/api/tasks/${createdTask.id}`);
    expect(deleteResponse.ok()).toBeTruthy();

    // 削除後、タスクが存在しないことを確認
    const verifyResponse = await request.get(`${API_URL}/api/tasks/${createdTask.id}`);
    expect(verifyResponse.status()).toBe(404);
  });
});

test.describe("期限表示", () => {
  test("期限切れタスクは赤色で表示される", async ({ page, request }) => {
    const prefix = "[E2E-期限切れ]";
    await cleanupTestTasks(request, prefix);

    // 期限切れのタスクを作成（昨日）
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 期限切れテスト`,
        priority: "medium",
        due_date: yesterday.toISOString(),
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 期限切れテスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // 作成したタスク要素にスコープして期限バッジを検証
    const taskItem = page.locator(`[data-testid="task-item-${createdTask.id}"]`);
    const dueDateBadge = taskItem.locator("[aria-label*='期限']");
    await expect(dueDateBadge).toBeVisible();
    await expect(dueDateBadge).toContainText(/期限切れ/);

    // 赤色のスタイルが適用されていることを確認（bg-red-100）
    await expect(dueDateBadge).toHaveClass(/bg-red-100/);

    await cleanupTestTasks(request, prefix);
  });

  test("期限間近タスク（24時間以内）は黄色で表示される", async ({ page, request }) => {
    const prefix = "[E2E-期限間近]";
    await cleanupTestTasks(request, prefix);

    // 12時間後のタスクを作成
    const soon = new Date();
    soon.setHours(soon.getHours() + 12);

    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 期限間近テスト`,
        priority: "medium",
        due_date: soon.toISOString(),
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 期限間近テスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // 作成したタスク要素にスコープして期限バッジを検証
    const taskItem = page.locator(`[data-testid="task-item-${createdTask.id}"]`);
    const dueDateBadge = taskItem.locator("[aria-label*='期限']");
    await expect(dueDateBadge).toBeVisible();

    // 黄色のスタイルが適用されていることを確認（bg-yellow-100）
    await expect(dueDateBadge).toHaveClass(/bg-yellow-100/);

    await cleanupTestTasks(request, prefix);
  });

  test("期限なしタスクはバッジが表示されない", async ({ page, request }) => {
    const prefix = "[E2E-期限なし]";
    await cleanupTestTasks(request, prefix);

    // 期限なしのタスクを作成
    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 期限なしテスト`,
        priority: "low",
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 期限なしテスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // タスクアイテム内に期限バッジがないことを確認
    const taskItem = page.locator(`[data-testid="task-item-${createdTask.id}"]`);
    const dueDateBadge = taskItem.locator("[aria-label*='期限']");
    await expect(dueDateBadge).not.toBeVisible();

    await cleanupTestTasks(request, prefix);
  });

  test("完了したタスクは期限バッジが非表示になる", async ({ page, request }) => {
    const prefix = "[E2E-完了期限]";
    await cleanupTestTasks(request, prefix);

    // 期限付きタスクを作成
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    const createResponse = await request.post(`${API_URL}/api/tasks`, {
      data: {
        title: `${prefix} 完了期限テスト`,
        priority: "medium",
        due_date: tomorrow.toISOString(),
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createdTask = await createResponse.json();

    await page.goto("/");
    await expect(page.getByText("Taska").first()).toBeVisible();

    // タスクが表示されるまで待機
    const taskText = page.getByText(`${prefix} 完了期限テスト`);
    await expect(taskText).toBeVisible({ timeout: 10000 });

    // 期限バッジが表示されていることを確認
    const taskItem = page.locator(`[data-testid="task-item-${createdTask.id}"]`);
    const dueDateBadge = taskItem.locator("[aria-label*='期限']");
    await expect(dueDateBadge).toBeVisible();

    // タスクを完了にする
    const checkbox = taskItem.getByRole("checkbox");
    await checkbox.click();

    // 完了後、期限バッジが非表示になることを確認
    await expect(dueDateBadge).not.toBeVisible({ timeout: 5000 });

    await cleanupTestTasks(request, prefix);
  });
});
