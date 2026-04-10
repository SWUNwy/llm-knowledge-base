"""Local usage tracking for offline scenarios."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass
class LocalLimits:
    """Cached tier limits from cloud."""

    max_compiles: int
    max_qa: int
    allowed_models: list[str]
    max_documents: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'LocalLimits':
        return cls(
            max_compiles=data.get('max_compiles', -1),
            max_qa=data.get('max_qa', -1),
            allowed_models=data.get('allowed_models', []),
            max_documents=data.get('max_documents')
        )


@dataclass
class UsageTracker:
    """Track local usage for current month."""

    compile_count: int = 0
    qa_count: int = 0

    def increment(self, action: str) -> None:
        if action == 'compile':
            self.compile_count += 1
        elif action == 'qa':
            self.qa_count += 1

    def can_perform(self, action: str, limits: LocalLimits) -> bool:
        if action == 'compile':
            return limits.max_compiles == -1 or self.compile_count < limits.max_compiles
        elif action == 'qa':
            return limits.max_qa == -1 or self.qa_count < limits.max_qa
        return False


class LocalUsageStore:
    """Persist usage tracking to local file."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.usage_file = vault_path / '.usage_tracking.json'
        self._tracker = UsageTracker()
        self._load()

    def _load(self) -> None:
        if not self.usage_file.exists():
            return

        try:
            data = json.loads(self.usage_file.read_text())
            # Check if data is from current month
            month_key = datetime.now(timezone.utc).strftime('%Y-%m')
            if data.get('month') == month_key:
                self._tracker = UsageTracker(
                    compile_count=data.get('compile_count', 0),
                    qa_count=data.get('qa_count', 0)
                )
            else:
                # New month - reset counters
                self._tracker = UsageTracker()
        except (json.JSONDecodeError, IOError):
            self._tracker = UsageTracker()

    def _save(self) -> None:
        month_key = datetime.now(timezone.utc).strftime('%Y-%m')
        data = {
            'month': month_key,
            'compile_count': self._tracker.compile_count,
            'qa_count': self._tracker.qa_count
        }
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        self.usage_file.write_text(json.dumps(data, indent=2))

    def increment(self, action: str) -> None:
        self._tracker.increment(action)
        self._save()

    def get_tracker(self) -> UsageTracker:
        return self._tracker

    def get_limits(self) -> LocalLimits | None:
        # Load from license cache
        license_file = self.vault_path / '.license_token'
        if not license_file.exists():
            return None

        try:
            data = json.loads(license_file.read_text())
            limits_data = data.get('limits')
            if limits_data:
                return LocalLimits.from_dict(limits_data)
        except (json.JSONDecodeError, IOError):
            pass
        return None
