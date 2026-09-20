export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.detail || payload?.error?.message || response.statusText;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return payload as T;
}

export const get = <T,>(path: string) => api<T>(path);

export const post = <T,>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export function usd(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function statusTone(status: string | undefined): string {
  const value = (status || "").toLowerCase();
  if (["closed", "matched", "approve", "completed", "pass", "tied", "clear", "paid"].some((item) => value.includes(item))) {
    return "ok";
  }
  if (["blocked", "hold", "fail", "unexplained", "exception", "human_review"].some((item) => value.includes(item))) {
    return "bad";
  }
  if (["review", "running", "open", "ready"].some((item) => value.includes(item))) {
    return "warn";
  }
  return "neutral";
}
