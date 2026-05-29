import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.database import get_db

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT id, email, name, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] or "",
        "createdAt": row["created_at"],
    }


def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def create_user(email: str, password: str, name: str = "") -> dict:
    user_id = uuid.uuid4().hex[:16]
    conn = get_db()
    conn.execute(
        "INSERT INTO users (id, email, password_hash, name) VALUES (?, ?, ?, ?)",
        (user_id, email.lower(), hash_password(password), name),
    )
    conn.commit()
    conn.close()
    return {"id": user_id, "email": email.lower(), "name": name}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    # #region agent log
    import json, time
    _log_path = "/Users/ayushgupta/Documents/Claude/Projects/CRM for ThoughtMint/mintos/.cursor/debug-cdc701.log"
    def _dbg(msg, data, hid):
        with open(_log_path, "a") as _f:
            _f.write(json.dumps({"sessionId":"cdc701","hypothesisId":hid,"location":"auth.py:get_current_user","message":msg,"data":data,"timestamp":int(time.time()*1000)}) + "\n")
    # #endregion
    if credentials is None:
        # #region agent log
        _dbg("auth rejected: no credentials", {"hasCredentials": False}, "D")
        # #endregion
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            # #region agent log
            _dbg("auth rejected: missing sub", {"hasSub": False}, "A")
            # #endregion
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        # #region agent log
        _dbg("auth rejected: jwt decode failed", {"errorType": type(e).__name__}, "A")
        # #endregion
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user_by_id(user_id)
    if not user:
        # #region agent log
        _dbg("auth rejected: user not found", {"userId": user_id}, "D")
        # #endregion
        raise HTTPException(status_code=401, detail="User not found")
    # #region agent log
    _dbg("auth success", {"userId": user["id"]}, "D")
    # #endregion
    return user
