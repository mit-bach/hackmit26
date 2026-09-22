"""Load project SKILL.md files and attach them to agent instructions.

These finance agents do not use the OpenAI Agents sandbox skill capability
(no filesystem browse tools). Skills are therefore injected into instructions
so the assigned procedure is available at run time.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Sequence

from skills.models import AgentSkillTrace, SkillRef

SKILLS_DIR = Path(__file__).resolve().parent
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_SECTIONS = (
    "Purpose",
    "When to Use",
    "Inputs / Evidence",
    "Procedure",
    "Decision Criteria",
    "Output Expectations",
    "Boundaries",
)

_VALIDATED = False


class SkillError(ValueError):
    """Invalid or missing skill definition."""


def content_hash(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def relative_skill_path(name: str) -> str:
    return f"skills/{name}/SKILL.md"


def validate_skill_name(name: str) -> None:
    if not name or not SKILL_NAME_RE.fullmatch(name):
        raise SkillError(f"Malformed skill name {name!r}")
    if Path(name).name != name or ".." in name:
        raise SkillError(f"Malformed skill path {name!r}")


def _parse_frontmatter(raw: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise SkillError(f"Invalid frontmatter line: {line!r}")
        key, _, value = stripped.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def parse_skill(path: Path, *, expected_name: str | None = None) -> dict:
    text = path.read_text()
    if not text.strip():
        raise SkillError(f"{path} is empty")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SkillError(f"{path} is missing YAML frontmatter")
    meta = _parse_frontmatter(match.group(1))
    body = match.group(2).strip()
    if not body:
        raise SkillError(f"{path} has an empty skill body")
    name = meta.get("name") or (expected_name or path.parent.name)
    description = meta.get("description", "")
    if not description:
        raise SkillError(f"{path} is missing a description")
    relpath = relative_skill_path(name)
    return {
        "name": name,
        "description": description,
        "status": meta.get("status", ""),
        "path": path,
        "relpath": relpath,
        "body": body,
        "raw": text,
        "content_hash": content_hash(text),
    }


def skill_path(name: str) -> Path:
    validate_skill_name(name)
    path = (SKILLS_DIR / name / "SKILL.md").resolve()
    skills_root = SKILLS_DIR.resolve()
    if path != skills_root / name / "SKILL.md":
        raise SkillError(f"Skill path escapes the skills directory: {name!r}")
    return path


def list_skill_names() -> list[str]:
    names = [
        child.name
        for child in sorted(SKILLS_DIR.iterdir())
        if child.is_dir() and (child / "SKILL.md").is_file()
    ]
    return names


def load_skill(name: str) -> dict:
    path = skill_path(name)
    if not path.is_file():
        raise SkillError(f"Unknown skill {name!r}: expected {relative_skill_path(name)}")
    skill = parse_skill(path, expected_name=name)
    if skill["name"] != name:
        raise SkillError(f"Skill folder {name!r} has frontmatter name {skill['name']!r}")
    return skill


def unique_skill_names(names: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    duplicates: list[str] = []
    for name in names:
        if name in seen:
            duplicates.append(name)
            continue
        seen.add(name)
        ordered.append(name)
    if duplicates:
        raise SkillError("Duplicate skill assignment: " + ", ".join(duplicates))
    return ordered


def load_skills(names: Sequence[str]) -> list[dict]:
    return [load_skill(name) for name in unique_skill_names(names)]


def missing_sections(body: str) -> list[str]:
    missing = []
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^## {re.escape(section)}\s*$", body, re.M):
            missing.append(section)
    return missing


def render_skills(names: Sequence[str]) -> str:
    if not names:
        return ""
    loaded = load_skills(names)
    listing = "Assigned skills:\n" + "\n".join(f"- {skill['name']}" for skill in loaded)
    blocks = [f"## Skill: {skill['name']}\n\n{skill['body']}" for skill in loaded]
    return listing + "\n\n" + "\n\n".join(blocks)


def compose_instructions(
    role: str,
    *,
    skills: Sequence[str] = (),
    safety: str = "",
) -> str:
    ensure_validated()
    parts = [role.strip()]
    rendered = render_skills(skills)
    if rendered:
        parts.append(rendered)
    if safety:
        parts.append(safety.strip())
    return "\n\n".join(parts)


def skill_was_injected(skill: dict, instructions: str) -> bool:
    if not instructions:
        return False
    return (
        f"## Skill: {skill['name']}" in instructions
        and f"- {skill['name']}" in instructions
        and skill["body"] in instructions
    )


def skill_usage_for(agent_name: str, instructions: str = "") -> AgentSkillTrace:
    from skills.assignments import skills_for

    try:
        assigned = skills_for(agent_name)
    except KeyError:
        return AgentSkillTrace(
            role=agent_name,
            load_errors=[f"No skill assignment registered for agent {agent_name!r}"],
        )

    refs: list[SkillRef] = []
    errors: list[str] = []
    seen: set[str] = set()
    for name in assigned:
        if name in seen:
            errors.append(f"Duplicate skill assignment: {name}")
            continue
        seen.add(name)
        try:
            skill = load_skill(name)
        except SkillError as exc:
            errors.append(str(exc))
            continue
        refs.append(
            SkillRef(
                name=skill["name"],
                path=skill["relpath"],
                content_hash=skill["content_hash"],
                injected=skill_was_injected(skill, instructions),
            )
        )
    return AgentSkillTrace(role=agent_name, skills=refs, load_errors=errors)


def usage_from_agent(agent) -> AgentSkillTrace:
    instructions = agent.instructions if isinstance(getattr(agent, "instructions", None), str) else ""
    return skill_usage_for(agent.name, instructions)


def ensure_validated() -> None:
    global _VALIDATED
    if _VALIDATED:
        return
    from skills.validate import validate_skill_system

    validate_skill_system()
    _VALIDATED = True
