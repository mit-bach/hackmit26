import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { checkHealth, isApiLive, lastRunSource, post, subscribeHealth, type RunSource } from "./api";
import { demoApi } from "./demoClient";

export function useHealth(): boolean {
  const [live, setLive] = useState(isApiLive());
  const location = useLocation();
  useEffect(() => subscribeHealth(setLive), []);
  useEffect(() => {
    void checkHealth();
    const timer = window.setInterval(() => {
      void checkHealth();
    }, 15000);
    return () => window.clearInterval(timer);
  }, [location.pathname]);
  return live;
}

export function useWorkflow(): {
  running: boolean;
  result: unknown;
  error: string | null;
  source: RunSource | null;
  run: (pathOrTask: string | (() => Promise<unknown>), body?: unknown) => Promise<unknown>;
  setResult: (value: unknown) => void;
  demoApi: typeof demoApi;
} {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<RunSource | null>(null);

  async function run(pathOrTask: string | (() => Promise<unknown>), body?: unknown): Promise<unknown> {
    setRunning(true);
    setError(null);
    try {
      const payload =
        typeof pathOrTask === "function" ? await pathOrTask() : await post(pathOrTask, body);
      setResult(payload);
      const tagged = payload as { _source?: RunSource; ok?: boolean; error?: { message?: string } };
      setSource(tagged?._source || lastRunSource());
      if (tagged?._source === "saved") {
        setError(null);
      } else if (tagged?.ok === false) {
        setError(tagged.error?.message || "Workflow failed");
      }
      return payload;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setResult({ ok: false, error: { message } });
      setSource(null);
      return null;
    } finally {
      setRunning(false);
    }
  }

  return { running, result, error, source, run, setResult, demoApi };
}
