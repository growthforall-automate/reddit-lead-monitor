import uuid
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.services import reddit_service, llm_service

router = APIRouter()


def get_all_settings() -> dict:
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] or "" for r in rows}


def row_to_item(row) -> dict:
    return {
        "id":              row["id"],
        "subreddit":       row["subreddit"] or "",
        "postId":          row["post_id"] or "",
        "postTitle":       row["post_title"] or "",
        "postUrl":         row["post_url"] or "",
        "postBody":        row["post_body"] or "",
        "author":          row["author"] or "",
        "postScore":       row["post_score"] or 0,
        "relevanceScore":  row["relevance_score"] or 0,
        "relevanceReason": row["relevance_reason"] or "",
        "painPoint":       row["pain_point"] or "",
        "dmDraft":         row["dm_draft"] or "",
        "status":          row["status"] or "new",
        "createdAt":       row["created_at"] or "",
    }


# ── GET queue ──────────────────────────────────────────────────────────────────
@router.get("")
def get_queue(status: Optional[str] = None):
    conn = get_db()
    if status and status != "all":
        rows = conn.execute(
            "SELECT * FROM reddit_queue WHERE status=? ORDER BY relevance_score DESC, created_at DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM reddit_queue ORDER BY relevance_score DESC, created_at DESC"
        ).fetchall()
    conn.close()
    return [row_to_item(r) for r in rows]


# ── GET stats ──────────────────────────────────────────────────────────────────
@router.get("/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM reddit_queue").fetchone()[0]
    by_status = conn.execute("SELECT status, COUNT(*) as cnt FROM reddit_queue GROUP BY status").fetchall()
    conn.close()
    stats = {r["status"]: r["cnt"] for r in by_status}
    return {"total": total, **stats}


# ── GET scan status (new endpoint to check last scan result) ───────────────────
@router.get("/scan/status")
def get_scan_status():
    """Returns the last scan log entry so the UI can show success/failure."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM scan_log ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            return {"ok": True, "last_scan": dict(row)}
        return {"ok": True, "last_scan": None}
    except Exception:
        conn.close()
        return {"ok": True, "last_scan": None}


# ── POST scan ──────────────────────────────────────────────────────────────────
@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    settings = get_all_settings()
    # FIX: also check for client_secret, not just client_id
    if not settings.get("reddit_client_id") or not settings.get("reddit_client_secret"):
        raise HTTPException(
            status_code=400,
            detail="Reddit credentials not configured. Add client_id and client_secret in Settings."
        )
    if not settings.get("reddit_username"):
        raise HTTPException(
            status_code=400,
            detail="Reddit username not configured. Go to Settings."
        )
    background_tasks.add_task(_run_scan, settings)
    return {"ok": True, "message": "Scan started in background"}


async def _run_scan(settings: dict):
    """
    FIX: scan_subreddits is synchronous (PRAW uses blocking HTTP).
    Wrap it in asyncio.to_thread() so it runs in a thread pool
    instead of blocking FastAPI's async event loop.
    """
    try:
        posts = await asyncio.to_thread(reddit_service.scan_subreddits, settings)
    except Exception as e:
        # FIX: errors are now logged clearly instead of silently swallowed
        print(f"[Scan] Reddit fetch failed: {e}")
        _log_scan(success=False, inserted=0, error=str(e))
        return

    conn = get_db()
    inserted = 0
    score_errors = 0

    for post in posts:
        existing = conn.execute(
            "SELECT id FROM reddit_queue WHERE post_id=?", (post["post_id"],)
        ).fetchone()
        if existing:
            continue

        try:
            scored = await llm_service.score_post(post, settings)
        except Exception as e:
            print(f"[Scan] LLM scoring failed for post {post['post_id']}: {e}")
            scored = {"score": 5.0, "reason": "Auto-score failed", "pain_point": "Unknown"}
            score_errors += 1

        item_id = uuid.uuid4().hex[:12]
        conn.execute("""
            INSERT INTO reddit_queue
                (id, subreddit, post_id, post_title, post_url, post_body, author, post_score,
                 relevance_score, relevance_reason, pain_point, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,'new')
        """, (
            item_id, post["subreddit"], post["post_id"], post["post_title"],
            post["post_url"], post["post_body"], post["author"], post["post_score"],
            scored.get("score", 5.0), scored.get("reason", ""), scored.get("pain_point", ""),
        ))
        inserted += 1

    conn.commit()
    conn.close()

    msg = f"Scan done — {inserted} new posts added"
    if score_errors:
        msg += f" ({score_errors} scoring errors, used defaults)"
    print(f"[Scan] {msg}")
    _log_scan(success=True, inserted=inserted, error=None)


def _log_scan(success: bool, inserted: int, error: Optional[str]):
    """Write scan result to scan_log table if it exists (best-effort)."""
    try:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                success INTEGER,
                inserted INTEGER,
                error TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "INSERT INTO scan_log (success, inserted, error) VALUES (?,?,?)",
            (1 if success else 0, inserted, error)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Scan] Could not write to scan_log: {e}")


# ── POST generate DM ───────────────────────────────────────────────────────────
@router.post("/{item_id}/generate")
async def generate_dm(item_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM reddit_queue WHERE id=?", (item_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Queue item not found")

    settings = get_all_settings()
    if not (settings.get("anthropic_api_key") or settings.get("openai_api_key") or
            settings.get("gemini_api_key") or settings.get("groq_api_key")):
        raise HTTPException(status_code=400, detail="LLM API key not configured. Go to Settings.")

    post = row_to_item(row)
    dm = await llm_service.generate_dm(post, settings)

    conn = get_db()
    conn.execute(
        "UPDATE reddit_queue SET dm_draft=?, status='generated', updated_at=datetime('now') WHERE id=?",
        (dm, item_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reddit_queue WHERE id=?", (item_id,)).fetchone()
    conn.close()
    return row_to_item(row)


# ── PUT update item (status, dm edit) ─────────────────────────────────────────
class QueueUpdate(BaseModel):
    status: Optional[str] = None
    dm_draft: Optional[str] = None


@router.put("/{item_id}")
def update_item(item_id: str, payload: QueueUpdate):
    conn = get_db()
    if payload.status:
        conn.execute(
            "UPDATE reddit_queue SET status=?, updated_at=datetime('now') WHERE id=?",
            (payload.status, item_id)
        )
    if payload.dm_draft is not None:
        conn.execute(
            "UPDATE reddit_queue SET dm_draft=?, updated_at=datetime('now') WHERE id=?",
            (payload.dm_draft, item_id)
        )
    conn.commit()
    row = conn.execute("SELECT * FROM reddit_queue WHERE id=?", (item_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row_to_item(row)


# ── DELETE item ────────────────────────────────────────────────────────────────
@router.delete("/{item_id}")
def delete_item(item_id: str):
    conn = get_db()
    conn.execute("DELETE FROM reddit_queue WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"ok": True}
