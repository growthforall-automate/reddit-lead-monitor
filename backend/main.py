import os
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.database import init_db
from backend.auth import get_current_user
from backend.routers import leads, brain, settings, reddit, auth
from backend.config import FRONTEND_DIR

app = FastAPI(title="MintOS API", version="1.0.0", docs_url="/api/docs")

# CORS — allows frontend dev server to talk to backend if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    print("\n🌿 MintOS is running → http://localhost:8000\n")


# ── API Routes ─────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(
    leads.router,
    prefix="/api/leads",
    tags=["Leads"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    brain.router,
    prefix="/api/brain",
    tags=["Brain"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    settings.router,
    prefix="/api/settings",
    tags=["Settings"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    reddit.router,
    prefix="/api/reddit",
    tags=["Reddit"],
    dependencies=[Depends(get_current_user)],
)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "app": "MintOS", "version": "1.0.0"}


# ── Serve React frontend ───────────────────────────────────────────────────────
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str = ""):
    # Don't intercept API routes
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"error": "Frontend not found. Check the frontend/ directory."}
