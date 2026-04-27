from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from web.services.auth_service import register, login, refresh_token

router = APIRouter(prefix="/api/auth")

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
async def auth_register(req: RegisterRequest):
    result = register(req.username, req.email, req.password)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.post("/login")
async def auth_login(req: LoginRequest):
    result = login(req.username, req.password)
    if result["status"] == "error":
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@router.get("/refresh-token")
async def auth_refresh_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[7:]
    result = refresh_token(token)
    if result["status"] == "error":
        raise HTTPException(status_code=401, detail=result["message"])

    return {"new_token": result["new_token"]}
