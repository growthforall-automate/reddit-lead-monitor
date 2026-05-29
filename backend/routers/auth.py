from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import (
    create_access_token,
    create_user,
    get_current_user,
    get_user_by_email,
    verify_password,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/register", status_code=201, response_model=AuthResponse)
def register(body: RegisterRequest):
    # #region agent log
    import json, time
    _log_path = "/Users/ayushgupta/Documents/Claude/Projects/CRM for ThoughtMint/mintos/.cursor/debug-cdc701.log"
    with open(_log_path, "a") as _f:
        _f.write(json.dumps({"sessionId":"cdc701","hypothesisId":"C","location":"auth.py:register","message":"register attempt","data":{"emailDomain": body.email.split("@")[-1] if "@" in body.email else "invalid","pwLen": len(body.password)},"timestamp":int(time.time()*1000)}) + "\n")
    # #endregion
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = create_user(email, body.password, body.name.strip())
    token = create_access_token(user["id"], user["email"])
    return {"token": token, "user": user}


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    # #region agent log
    import json, time
    _log_path = "/Users/ayushgupta/Documents/Claude/Projects/CRM for ThoughtMint/mintos/.cursor/debug-cdc701.log"
    with open(_log_path, "a") as _f:
        _f.write(json.dumps({"sessionId":"cdc701","hypothesisId":"C","location":"auth.py:login","message":"login attempt","data":{"emailDomain": body.email.split("@")[-1] if "@" in body.email else "invalid"},"timestamp":int(time.time()*1000)}) + "\n")
    # #endregion
    email = body.email.strip().lower()
    user = get_user_by_email(email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], user["email"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"] or "",
        },
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user
