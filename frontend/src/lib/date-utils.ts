import {
  formatDistanceToNow,
  isPast,
  differenceInHours,
  isToday,
  isTomorrow,
  format,
} from "date-fns";
import { ja } from "date-fns/locale";

export type DueDateStatus = "overdue" | "urgent" | "upcoming" | "normal" | null;

/**
 * 期限の状態を判定
 * - overdue: 期限切れ
 * - urgent: 24時間以内
 * - upcoming: 3日以内
 * - normal: それ以外
 */
export function getDueDateStatus(dueDate: string | null): DueDateStatus {
  if (!dueDate) return null;

  const due = new Date(dueDate);
  const now = new Date();

  if (isPast(due)) return "overdue";

  const hoursUntil = differenceInHours(due, now);
  if (hoursUntil <= 24) return "urgent";
  if (hoursUntil <= 72) return "upcoming";

  return "normal";
}

/**
 * 期限を日本語の相対表記でフォーマット
 */
export function formatDueDate(dueDate: string | null): string | null {
  if (!dueDate) return null;

  const due = new Date(dueDate);
  const now = new Date();

  if (isToday(due)) {
    return `今日 ${format(due, "HH:mm")}`;
  }

  if (isTomorrow(due)) {
    return `明日 ${format(due, "HH:mm")}`;
  }

  if (isPast(due)) {
    return formatDistanceToNow(due, { locale: ja, addSuffix: true }) + "に期限切れ";
  }

  const hoursUntil = differenceInHours(due, now);
  if (hoursUntil <= 72) {
    return formatDistanceToNow(due, { locale: ja, addSuffix: true });
  }

  return format(due, "M月d日 HH:mm", { locale: ja });
}
