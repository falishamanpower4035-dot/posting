import json
from pathlib import Path
from typing import Dict, Any


STATE_FILE = Path("data/pipeline_state.json")


DEFAULT = {
    "posts": {},  # post_id -> {stage: str, checksum: str, youtube_id: str, fb_id: str}
}


def _load() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT.copy()


def _save(state: Dict[str, Any]):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def set_stage(post_id: str, stage: str):
    state = _load()
    post = state["posts"].get(post_id, {})
    post["stage"] = stage
    state["posts"][post_id] = post
    _save(state)


def get_stage(post_id: str) -> str:
    state = _load()
    return state["posts"].get(post_id, {}).get("stage", "pending")


def set_published_id(post_id: str, platform: str, value: str):
    state = _load()
    post = state["posts"].get(post_id, {})
    key = f"{platform}_id"
    post[key] = value
    state["posts"][post_id] = post
    _save(state)


def get_published_id(post_id: str, platform: str) -> str:
    state = _load()
    key = f"{platform}_id"
    return state["posts"].get(post_id, {}).get(key)


