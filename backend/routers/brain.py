import os
from fastapi import APIRouter, HTTPException
from backend.config import BRAIN_DIR
from backend.models import BrainFile

router = APIRouter()

ALLOWED_FILES = {"context.md", "icp.md", "pain_points.md", "voice.md", "learnings.md"}

FILE_META = {
    "context.md":      {"label": "Product Context",   "icon": "🌿", "desc": "What MintOS & ThoughtMint are, current stage, goals"},
    "icp.md":          {"label": "Ideal Customer",    "icon": "🎯", "desc": "Who you're trying to reach — titles, situations, goals"},
    "pain_points.md":  {"label": "Pain Points",       "icon": "⚡", "desc": "Exact language your ICP uses when they're frustrated"},
    "voice.md":        {"label": "Brand Voice",       "icon": "🎙️", "desc": "How Ayush writes — tone, style, phrases to use/avoid"},
    "learnings.md":    {"label": "Learnings",         "icon": "📈", "desc": "What's working, what's not — updated as you grow"},
}


def safe_path(filename: str) -> str:
    if filename not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail=f"Invalid file: {filename}")
    return os.path.join(BRAIN_DIR, filename)


# ── GET all brain files ────────────────────────────────────────────────────────
@router.get("")
def list_brain_files():
    result = []
    for filename in ALLOWED_FILES:
        path = os.path.join(BRAIN_DIR, filename)
        content = ""
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
        meta = FILE_META.get(filename, {})
        result.append({
            "filename": filename,
            "label": meta.get("label", filename),
            "icon": meta.get("icon", "📄"),
            "desc": meta.get("desc", ""),
            "content": content,
            "wordCount": len(content.split()),
        })
    return result


# ── GET single brain file ──────────────────────────────────────────────────────
@router.get("/{filename}")
def get_brain_file(filename: str):
    path = safe_path(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r") as f:
        content = f.read()
    meta = FILE_META.get(filename, {})
    return {"filename": filename, "label": meta.get("label", filename), "content": content}


# ── PUT update brain file ──────────────────────────────────────────────────────
@router.put("/{filename}")
def update_brain_file(filename: str, payload: BrainFile):
    path = safe_path(filename)
    os.makedirs(BRAIN_DIR, exist_ok=True)
    with open(path, "w") as f:
        f.write(payload.content)
    return {"ok": True, "filename": filename, "wordCount": len(payload.content.split())}
