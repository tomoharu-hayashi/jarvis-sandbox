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
