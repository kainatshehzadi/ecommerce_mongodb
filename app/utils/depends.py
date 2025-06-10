from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from app.db.database import get_db
from app.routers import admin
from app.utils.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "secretkey")
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload 
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return payload

async def require_customer(token: str = Depends(oauth2_scheme)):
    db = get_db()
    payload = decode_access_token(token)

    print("Decoded Token Payload:", payload)

    user = await db.users.find_one({"email": payload.get("sub")})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can access this route")

    user["id"] = str(user["_id"])
    return user