function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function errorMessage(payload: any, fallback: string): string {
  const message = payload?.detail || payload?.error?.message || fallback;
  return typeof message === "string" ? message : JSON.stringify(message);
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
        ...init,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const err = new Error(errorMessage(payload, response.statusText));
        if ([500, 502, 503, 504].includes(response.status) && attempt < 2) {
          lastError = err;
          await sleep(400 * (attempt + 1));
          continue;
        }
        throw err;
      }
      return payload as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      const retryable =
        lastError.message === "Failed to fetch" ||
        lastError.message === "Internal Server Error" ||
        lastError.name === "TypeError";
      if (attempt < 2 && retryable) {
        await sleep(400 * (attempt + 1));
        continue;
      }
      throw lastError;
    }
  }
  throw lastError || new Error("Request failed");
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
  if (["blocked", "hold", "fail", "unexplained", "exception", "human_review", "cannot", "duplicate"].some((item) => value.includes(item))) {
    return "bad";
  }
  if (["review", "running", "open", "ready"].some((item) => value.includes(item))) {
    return "warn";
  }
  return "neutral";
}
