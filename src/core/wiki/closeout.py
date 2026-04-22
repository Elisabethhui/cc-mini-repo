"""
Closeout record storage for Phase 6.

This module persists a single closeout record in JSON and Markdown form under
the wiki reports tree. It does not touch source files or git state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    slug = []
    for char in value.strip().lower():
        if char.isalnum():
            slug.append(char)
        else:
            slug.append("-")
    result = "".join(slug).strip("-")
    while "--" in result:
        result = result.replace("--", "-")
    return result or "item"


@dataclass
class CloseoutRecord:
    task_id: str
    phase_name: str
    verification_status: str
    review_status: str
    commit_status: str
    commit_hash: str | None
    ready_for_audit: bool
    residual_risks: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CloseoutRecord:
        residual_risks = data.get("residual_risks", [])
        if residual_risks is None:
            residual_risks_list: list[str] = []
        elif isinstance(residual_risks, list):
            residual_risks_list = [str(item) for item in residual_risks]
        elif isinstance(residual_risks, tuple):
            residual_risks_list = [str(item) for item in residual_risks]
        else:
            residual_risks_list = [str(residual_risks)]

        commit_hash = data.get("commit_hash")
        if commit_hash == "":
            commit_hash = None

        return cls(
            task_id=str(data.get("task_id", "")),
            phase_name=str(data.get("phase_name", "")),
            verification_status=str(data.get("verification_status", "")),
            review_status=str(data.get("review_status", "")),
            commit_status=str(data.get("commit_status", "")),
            commit_hash=commit_hash,
            ready_for_audit=bool(data.get("ready_for_audit", False)),
            residual_risks=residual_risks_list,
            created_at=str(data.get("created_at", _utc_now_iso())),
            updated_at=str(data.get("updated_at", _utc_now_iso())),
        )


class CloseoutStore:
    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.closeout_dir = self.workspace / ".cc-mini" / "wiki" / "reports" / "closeout"
        self.closeout_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: CloseoutRecord) -> Path:
        record.updated_at = _utc_now_iso()
        stem = self._build_stem(record, record.updated_at)
        json_path = self.closeout_dir / f"{stem}.json"
        md_path = self.closeout_dir / f"{stem}.md"

        json_path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self.render_markdown(record), encoding="utf-8")
        return json_path

    def load(self, stem: str) -> CloseoutRecord:
        json_path = self.closeout_dir / f"{stem}.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return CloseoutRecord.from_dict(data)

    def load_latest(self, task_id: str | None = None) -> CloseoutRecord | None:
        records = self._load_records(task_id=task_id)
        if not records:
            return None
        records.sort(key=self._record_sort_key, reverse=True)
        return records[0]

    def render_markdown(self, record: CloseoutRecord) -> str:
        risks = record.residual_risks or []
        risk_lines = "\n".join(f"- {item}" for item in risks) if risks else "- None"
        commit_hash = record.commit_hash or "None"
        ready = "yes" if record.ready_for_audit else "no"

        return (
            "# Closeout Record\n\n"
            f"- Task ID: {record.task_id}\n"
            f"- Phase: {record.phase_name}\n"
            f"- Verification Status: {record.verification_status}\n"
            f"- Review Status: {record.review_status}\n"
            f"- Commit Status: {record.commit_status}\n"
            f"- Commit Hash: `{commit_hash}`\n"
            f"- Ready for Audit: {ready}\n"
            f"- Created At: {record.created_at}\n"
            f"- Updated At: {record.updated_at}\n\n"
            "## Residual Risks\n\n"
            f"{risk_lines}\n"
        )

    def _load_records(self, task_id: str | None = None) -> list[CloseoutRecord]:
        records: list[CloseoutRecord] = []
        for path in self.closeout_dir.glob("*.json"):
            try:
                record = CloseoutRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if task_id is not None and record.task_id != task_id:
                continue
            records.append(record)
        return records

    def _record_sort_key(self, record: CloseoutRecord) -> tuple[str, str, str]:
        return (record.updated_at, record.created_at, record.task_id)

    def _build_stem(self, record: CloseoutRecord, timestamp: str) -> str:
        timestamp_slug = timestamp.replace(":", "").replace("+", "").replace("-", "").replace(".", "")
        return "__".join(
            [
                timestamp_slug,
                _slugify(record.task_id),
                _slugify(record.phase_name),
            ]
        )
