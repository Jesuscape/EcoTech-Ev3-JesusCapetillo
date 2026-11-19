import json
from pathlib import Path
from typing import Any


class LocalStorage:
    """Gestiona la persistencia local en archivos JSON de manera segura."""

    @staticmethod
    def ensure_directory(file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_json(cls, file_path: Path, default: Any) -> Any:
        cls.ensure_directory(file_path)
        if not file_path.exists():
            return default
        try:
            with file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return default

    @classmethod
    def save_json(cls, file_path: Path, data: Any) -> bool:
        cls.ensure_directory(file_path)
        try:
            with file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            return True
        except OSError:
            return False

    @classmethod
    def append_record(cls, file_path: Path, record: dict[str, Any]) -> bool:
        records = cls.load_json(file_path, default=[])
        if not isinstance(records, list):
            records = []
        records.append(record)
        return cls.save_json(file_path, records)
