from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db

router = APIRouter()

SETTINGS_KEYS = [
    "llm_provider",
    "llm_api_key",
    "llm_model",
    "reddit_client_id",
    "reddit_client_secret",
    "reddit_username",
    "reddit_password",
    "reddit_user_agent",
    "reddit_subreddits",
    "reddit_min_score",
    "reddit_post_limit",
]


def load_settings(db) -> dict:
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_username: Optional[str] = None
    reddit_password: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    reddit_subreddits: Optional[str] = None
    reddit_min_score: Optional[str] = None
    reddit_post_limit: Optional[str] = None


@router.get("")
def get_settings():
    with get_db() as db:
        return load_settings(db)


@router.put("")
def update_settings(body: SettingsUpdate):
    data = body.model_dump(exclude_none=False)
    with get_db() as db:
        for key in SETTINGS_KEYS:
            val = data.get(key)
            if val is not None:
                # INSERT OR REPLACE ensures the row is always written
                db.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(val)),
                )
            else:
                # If value is empty string, still save it (user cleared the field)
                if key in data:
                    db.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (key, ""),
                    )
        db.commit()
        return load_settings(db)
