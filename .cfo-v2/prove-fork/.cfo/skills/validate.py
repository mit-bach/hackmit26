"""Fail fast if skill files, assignments, or the registry disagree."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from skills.assignments import AGENT_SKILLS
from skills.loader import (
    SKILLS_DIR,
    SkillError,
    list_skill_names,
    load_skill,
    unique_skill_names,
    validate_skill_name,
)

REGISTRY_HEADING = "## Registry"
REGISTRY_END_HEADING = "## Agents with no assigned skills"


def registry_skill_names(text: str | None = None) -> list[str]:
    raw = text if text is not None else (SKILLS_DIR / "README.md").read_text()
    if REGISTRY_HEADING not in raw:
        raise SkillError("skills/README.md is missing a Registry section")
    table = raw.split(REGISTRY_HEADING, 1)[1]
    if REGISTRY_END_HEADING in table:
        table = table.split(REGISTRY_END_HEADING, 1)[0]
    return re.findall(r"^\| ([a-z][a-z0-9-]*) \|", table, re.M)


def _collect_errors(
    assignments: Mapping[str, Sequence[str]],
    *,
    skills_dir: Path,
    registry_text: str | None,
    known_agents: Sequence[str] | None,
) -> list[str]:
    errors: list[str] = []
    on_disk = [
        child.name
        for child in sorted(skills_dir.iterdir())
        if child.is_dir() and (child / "SKILL.md").is_file()
    ]
    assigned: list[str] = []

    for agent_name, skill_names in assignments.items():
        if not agent_name or not str(agent_name).strip():
            errors.append("Assignment references an empty agent identifier")
            continue
        try:
            unique_skill_names(skill_names)
        except SkillError as exc:
            errors.append(f"{agent_name}: {exc}")
        for name in skill_names:
            assigned.append(name)
            try:
                validate_skill_name(name)
            except SkillError as exc:
                errors.append(f"{agent_name}: {exc}")
                continue
            path = skills_dir / name / "SKILL.md"
            if not path.is_file():
                errors.append(
                    f"{agent_name}: assigned skill {name!r} does not exist "
                    f"(expected skills/{name}/SKILL.md)"
                )
                continue
            if skills_dir == SKILLS_DIR:
                try:
                    load_skill(name)
                except SkillError as exc:
                    errors.append(str(exc))
            else:
                try:
                    from skills.loader import parse_skill

                    parsed = parse_skill(path, expected_name=name)
                    if parsed["name"] != name:
                        errors.append(
                            f"Skill folder {name!r} has frontmatter name {parsed['name']!r}"
                        )
                except SkillError as exc:
                    errors.append(str(exc))

    try:
        registered = set(registry_skill_names(registry_text))
    except SkillError as exc:
        errors.append(str(exc))
        registered = set()

    disk_set = set(on_disk)
    assigned_set = set(assigned)
    if disk_set != assigned_set:
        errors.append(
            "Skill files and assignments disagree: "
            f"only-on-disk={sorted(disk_set - assigned_set)} "
            f"only-assigned={sorted(assigned_set - disk_set)}"
        )
    if registered and registered != assigned_set:
        errors.append(
            "Skill registry and assignments disagree: "
            f"only-in-registry={sorted(registered - assigned_set)} "
            f"only-assigned={sorted(assigned_set - registered)}"
        )

    if known_agents is not None:
        known = set(known_agents)
        extra = sorted(set(assignments) - known)
        missing = sorted(known - set(assignments))
        if extra:
            errors.append("Assignment references unknown agent identifier(s): " + ", ".join(extra))
        if missing:
            errors.append("Known agent(s) missing from assignments: " + ", ".join(missing))
    return errors


def validate_skill_system(
    assignments: Mapping[str, Sequence[str]] | None = None,
    *,
    skills_dir: Path | None = None,
    registry_text: str | None = None,
    known_agents: Sequence[str] | None = None,
) -> None:
    """Raise SkillError if files, assignments, or the registry are inconsistent."""
    errors = _collect_errors(
        assignments if assignments is not None else AGENT_SKILLS,
        skills_dir=skills_dir or SKILLS_DIR,
        registry_text=registry_text,
        known_agents=known_agents,
    )
    if errors:
        raise SkillError("Skill system is invalid:\n- " + "\n- ".join(errors))
