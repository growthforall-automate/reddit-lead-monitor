import sqlite3
from backend.config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # ── Leads ─────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL DEFAULT '',
            email       TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            company     TEXT DEFAULT '',
            role        TEXT DEFAULT '',
            value       TEXT DEFAULT '',
            source      TEXT DEFAULT 'Manual',
            stage       TEXT DEFAULT 'new',
            notes       TEXT DEFAULT '',
            follow_up   TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Settings (key-value store) ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT DEFAULT ''
        )
    """)

    # ── Seed default settings if missing ──────────────────────────────────────
    defaults = {
        "llm_provider": "claude",
        "llm_model": "claude-opus-4-6",
        "anthropic_api_key": "",
        "openai_api_key": "",
        "gemini_api_key": "",
        "groq_api_key": "",
        "reddit_client_id": "",
        "reddit_client_secret": "",
        "reddit_username": "",
        "reddit_password": "",
        "reddit_user_agent": "MintOS/1.0 by ThoughtMint (thoughtmint.ai)",
        "reddit_subreddits": "entrepreneur,indiehackers,SaaS,linkedin,contentmarketing,personalbranding,marketing,blogging",
        "reddit_min_score": "3",
        "reddit_scan_limit": "25",
    }
    for key, value in defaults.items():
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    # ── Users ──────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name          TEXT DEFAULT '',
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Reddit Queue ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS reddit_queue (
            id               TEXT PRIMARY KEY,
            subreddit        TEXT DEFAULT '',
            post_id          TEXT UNIQUE,
            post_title       TEXT DEFAULT '',
            post_url         TEXT DEFAULT '',
            post_body        TEXT DEFAULT '',
            author           TEXT DEFAULT '',
            post_score       INTEGER DEFAULT 0,
            relevance_score  REAL DEFAULT 0,
            relevance_reason TEXT DEFAULT '',
            pain_point       TEXT DEFAULT '',
            dm_draft         TEXT DEFAULT '',
            status           TEXT DEFAULT 'new',
            created_at       TEXT DEFAULT (datetime('now')),
            updated_at       TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
