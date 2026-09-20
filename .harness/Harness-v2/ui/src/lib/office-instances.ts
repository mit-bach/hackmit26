/** Saved office desks — not the model engine picker (`InstanceInfo` / `/api/instances`). */
import { useCallback, useEffect, useState } from "react";

import {
  api,
  useStore,
  type AppState,
  type Bot,
  type Group,
  type OfficeDesk,
  type OfficeInstanceRecord,
} from "@/state/store";

export type OfficeInstance = OfficeInstanceRecord;

export type OfficeInstancesResponse = OfficeDesk;

export interface CreatedOfficeInstanceResponse extends OfficeDesk {
  readonly instance: OfficeInstanceRecord;
}

export interface OfficeInstancesHook {
  readonly currentId: string;
  readonly instances: readonly OfficeInstanceRecord[];
  readonly busy: boolean;
  readonly error: string | null;
  readonly select: (id: string) => Promise<void>;
  readonly create: (name: string) => Promise<boolean>;
}

function deskFromResponse(body: OfficeDesk): OfficeDesk {
  return {
    currentId: body.currentId,
    instances: [...body.instances],
    computerRoot: body.computerRoot,
  };
}

export function useOfficeInstances(): OfficeInstancesHook {
  const { state, dispatch } = useStore();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentId = state.office.currentId;
  const instances = state.office.instances;

  useEffect(() => {
    if (instances.length > 0) {
      return;
    }
    let alive = true;
    void (async (): Promise<void> => {
      try {
        const body = await api<OfficeDesk>("/api/office-instances");
        if (!alive) {
          return;
        }
        dispatch({ type: "officePatched", office: deskFromResponse(body) });
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
  }, [dispatch, instances.length]);

  const select = useCallback(
    async (id: string): Promise<void> => {
      if (id.length === 0 || id === currentId) {
        return;
      }
      setBusy(true);
      setError(null);
      try {
        const selected = await api<OfficeDesk>(`/api/office-instances/${encodeURIComponent(id)}/select`, {
          method: "POST",
        });
        const snapshot = await api<{
          bots: Bot[];
          groups?: Group[];
          sections?: string[];
          computerControl?: Record<string, { held: boolean; helpReason: string | null }>;
          botQueuedMessages?: AppState["pendingQueued"];
          office?: OfficeDesk;
        }>("/api/bots");
        dispatch({
          type: "hydrate",
          bots: snapshot.bots,
          groups: snapshot.groups ?? [],
          sections: snapshot.sections ?? [],
          computerControl: snapshot.computerControl ?? {},
          botQueuedMessages: snapshot.botQueuedMessages,
          office: deskFromResponse(snapshot.office ?? selected),
        });
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
      } finally {
        setBusy(false);
      }
    },
    [currentId, dispatch],
  );

  const create = useCallback(
    async (name: string): Promise<boolean> => {
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
        dispatch({
          type: "officePatched",
          office: {
            currentId: created.currentId,
            instances: [...created.instances],
            computerRoot: state.office.computerRoot,
          },
        });
        return true;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
        return false;
      } finally {
        setBusy(false);
      }
    },
    [dispatch, state.office.computerRoot],
  );

  return { currentId, instances, busy, error, select, create };
}
