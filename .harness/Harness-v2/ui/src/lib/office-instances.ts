/** Saved office desks — not the model engine picker (`InstanceInfo` / `/api/instances`). */
import { useCallback, useEffect, useState } from "react";

import { api } from "@/state/store";

export interface OfficeInstance {
  readonly id: string;
  readonly name: string;
  readonly computerRel: string;
  readonly createdAt: string;
}

export interface OfficeInstancesResponse {
  readonly currentId: string;
  readonly instances: readonly OfficeInstance[];
  readonly computerRoot?: string;
}

export interface CreatedOfficeInstanceResponse extends OfficeInstancesResponse {
  readonly instance: OfficeInstance;
}

export interface OfficeInstancesHook {
  readonly currentId: string;
  readonly instances: readonly OfficeInstance[];
  readonly busy: boolean;
  readonly error: string | null;
  readonly select: (id: string) => Promise<void>;
  readonly create: (name: string) => Promise<boolean>;
}

function reloadDesk(): void {
  window.location.reload();
}

export function useOfficeInstances(): OfficeInstancesHook {
  const [currentId, setCurrentId] = useState("");
  const [instances, setInstances] = useState<readonly OfficeInstance[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void (async (): Promise<void> => {
      try {
        const body = await api<OfficeInstancesResponse>("/api/office-instances");
        if (!alive) {
          return;
        }
        setCurrentId(body.currentId);
        setInstances(body.instances);
      } catch (cause) {
        if (!alive) {
          return;
        }
        setError(cause instanceof Error ? cause.message : String(cause));
      }
    })();
    return (): void => {
      alive = false;
    };
  }, []);

  const select = useCallback(async (id: string): Promise<void> => {
    if (id.length === 0 || id === currentId) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api(`/api/office-instances/${encodeURIComponent(id)}/select`, { method: "POST" });
      reloadDesk();
    } catch (cause) {
      setBusy(false);
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }, [currentId]);

  const create = useCallback(async (name: string): Promise<boolean> => {
    const trimmed = name.trim();
    if (trimmed.length === 0) {
      setError("name required");
      return false;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await api<CreatedOfficeInstanceResponse>("/api/office-instances", {
        method: "POST",
        body: JSON.stringify({ name: trimmed }),
      });
      await api(`/api/office-instances/${encodeURIComponent(created.instance.id)}/select`, {
        method: "POST",
      });
      reloadDesk();
      return true;
    } catch (cause) {
      setBusy(false);
      setError(cause instanceof Error ? cause.message : String(cause));
      return false;
    }
  }, []);

  return { currentId, instances, busy, error, select, create };
}
