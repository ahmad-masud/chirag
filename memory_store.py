import json
import os
from pathlib import Path
from threading import Lock


_DEFAULT_MEMORY_FILE = Path(__file__).with_name(".chirag_memory.json")
_MEMORY_FILE = Path(os.getenv("CHIRAG_MEMORY_FILE", str(_DEFAULT_MEMORY_FILE)))
_LOCK = Lock()


def _load_data() -> dict:
    if not _MEMORY_FILE.exists():
        return {"server_contexts": {}}

    try:
        with _MEMORY_FILE.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return {"server_contexts": {}}

    if not isinstance(data, dict):
        return {"server_contexts": {}}

    data.setdefault("server_contexts", {})
    if not isinstance(data["server_contexts"], dict):
        data["server_contexts"] = {}
    return data


def _save_data(data: dict) -> None:
    _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = _MEMORY_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2, sort_keys=True)

    temp_file.replace(_MEMORY_FILE)


def get_server_contexts() -> dict:
    with _LOCK:
        data = _load_data()
        return {
            server_id: list(context_list)
            for server_id, context_list in data["server_contexts"].items()
            if isinstance(context_list, list)
        }


def get_context_list(server_id: int) -> list[str]:
    server_contexts = get_server_contexts()
    return server_contexts.get(str(server_id), [])


def add_context(server_id: int, note: str) -> bool:
    clean_note = note.strip()
    if not clean_note:
        return False

    with _LOCK:
        data = _load_data()
        server_contexts = data["server_contexts"]
        server_key = str(server_id)
        server_notes = server_contexts.setdefault(server_key, [])

        if not isinstance(server_notes, list):
            server_notes = []
            server_contexts[server_key] = server_notes

        server_notes.append(clean_note)
        _save_data(data)
        return True


def remove_context(server_id: int, index: int) -> bool:
    with _LOCK:
        data = _load_data()
        server_contexts = data["server_contexts"]
        server_key = str(server_id)
        server_notes = server_contexts.get(server_key)

        if not isinstance(server_notes, list) or not (0 < index <= len(server_notes)):
            return False

        server_notes.pop(index - 1)
        if server_notes:
            server_contexts[server_key] = server_notes
        else:
            server_contexts.pop(server_key, None)

        _save_data(data)
        return True


def clear_context(server_id: int) -> None:
    with _LOCK:
        data = _load_data()
        data["server_contexts"].pop(str(server_id), None)
        _save_data(data)