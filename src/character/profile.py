"""캐릭터 프로필 데이터 로딩."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_profile(character_id: str = "sherlock_holmes") -> dict:
    """저장된 캐릭터 프로필을 로드."""
    path = DATA_DIR / "profiles" / f"{character_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))
