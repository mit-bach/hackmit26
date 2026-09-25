import { BookOpen } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { api, type Bot } from "@/state/store";
import { Switch } from "../SettingsPrimitives";

interface ManagedSkill {
  readonly name: string;
  readonly description: string;
  readonly enabled: boolean;
  readonly source: string;
  readonly warnings: readonly string[];
}

interface SkillsListBody {
  readonly skills?: readonly ManagedSkill[];
}

interface SkillTextBody {
  readonly text?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseSkills(body: unknown): ManagedSkill[] {
  if (!isRecord(body) || !Array.isArray(body.skills)) {
    return [];
  }
  return body.skills.filter(
    (row): row is ManagedSkill =>
      isRecord(row) && typeof row.name === "string" && typeof row.description === "string",
  );
}

export function SkillsSection({ bot }: { readonly bot: Bot }): React.ReactElement {
  const [skills, setSkills] = useState<ManagedSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState("");
  const [error, setError] = useState("");
  const [viewing, setViewing] = useState<{ name: string; text: string } | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  const refresh = async (cancelled?: () => boolean): Promise<void> => {
    try {
      const body = await api<SkillsListBody>(`/api/bots/${bot.id}/skills`);
      if (cancelled?.()) {
        return;
      }
      setSkills(parseSkills(body));
      setError("");
    } catch (cause: unknown) {
      if (!cancelled?.()) {
        setError(cause instanceof Error ? cause.message : "Could not load skills.");
      }
    } finally {
      if (!cancelled?.()) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setViewing(null);
    void refresh(() => cancelled);
    return () => {
      cancelled = true;
    };
  }, [bot.id]);

  useEffect(() => {
    if (!viewing) {
      return;
    }
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.focus();
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        event.preventDefault();
        setViewing(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [viewing]);

  const toggle = async (skill: ManagedSkill): Promise<void> => {
    setWorking(skill.name);
    setError("");
    try {
      await api(`/api/bots/${bot.id}/skills/${encodeURIComponent(skill.name)}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: !skill.enabled }),
      });
      await refresh();
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Could not update this skill.");
    } finally {
      setWorking("");
    }
  };

  const view = async (skill: ManagedSkill): Promise<void> => {
    setError("");
    try {
      const result = await api<SkillTextBody>(
        `/api/bots/${bot.id}/skills/${encodeURIComponent(skill.name)}`,
      );
      setViewing({ name: skill.name, text: result.text ?? "" });
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Could not read SKILL.md.");
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl bg-card p-4">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-ink-secondary" />
          <div className="text-[15px] font-medium text-ink">Skills</div>
        </div>
        <div className="mt-1 text-[12px] leading-relaxed text-ink-secondary">
          Grant or revoke names on this Bot’s roster record. Files live at Computer/skills/&lt;name&gt;/SKILL.md.
          Copy a skill onto this Computer, then enable it. There is no GitHub import.
        </div>

        {loading ? (
          <div className="mt-3 text-[12px] text-ink-secondary">Loading…</div>
        ) : skills.length === 0 ? (
          <div className="mt-3 rounded-lg bg-inset px-3 py-2 text-[12px] text-ink-secondary">
            No SKILL.md on this Computer. Add Computer/skills/&lt;name&gt;/SKILL.md, then grant it here.
          </div>
        ) : (
          <div className="mt-3 divide-y divide-hairline/40 overflow-hidden rounded-lg border border-hairline/40">
            {skills.map((skill) => (
              <div key={skill.name} className="px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => void view(skill)} className="min-w-0 flex-1 text-left">
                    <div className="truncate font-mono text-[12.5px] text-ink">{skill.name}</div>
                    <div className="mt-0.5 line-clamp-2 text-[11.5px] text-ink-secondary">{skill.description}</div>
                  </button>
                  <Switch
                    checked={skill.enabled}
                    aria-label={`${skill.enabled ? "Revoke" : "Grant"} ${skill.name}`}
                    disabled={working === skill.name}
                    onClick={() => void toggle(skill)}
                  />
                </div>
                {skill.warnings.length > 0 && (
                  <div className="mt-1 text-[10.5px] text-warning">{skill.warnings.join(" · ")}</div>
                )}
              </div>
            ))}
          </div>
        )}
        {error ? <div className="mt-2 text-[12px] text-danger">{error}</div> : null}
      </div>

      {viewing && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 p-4">
          <div
            ref={dialogRef}
            role="dialog"
            aria-labelledby="skill-md-title"
            tabIndex={-1}
            className="max-h-[80vh] w-full max-w-lg overflow-hidden rounded-2xl border border-hairline/40 bg-panel"
          >
            <div className="flex items-center justify-between border-b border-hairline/40 px-4 py-3">
              <div id="skill-md-title" className="truncate font-mono text-[13px] text-ink">
                {viewing.name}/SKILL.md
              </div>
              <button
                type="button"
                onClick={() => setViewing(null)}
                className="rounded-md px-2 py-1 text-[12px] text-ink-secondary hover:bg-raised"
              >
                Close
              </button>
            </div>
            <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap px-4 py-3 text-[12px] text-ink">
              {viewing.text.length > 0 ? viewing.text : "Empty SKILL.md"}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
