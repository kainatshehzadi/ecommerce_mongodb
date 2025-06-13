from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.db.database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from dotenv import load_dotenv
load_dotenv()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in the environment")
ALGORITHM = "HS256"
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    #print("Incoming token:", token) 

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        #print("Decoded token payload:", payload)  
        if email is None:
            raise credentials_exception

        user = await db.users.find_one({"email": email})
        #print("Fetched user:", user)  
        if not user:
            raise credentials_exception
        return user
    except JWTError as e:
        #print("JWT Error:", e) 
        raise credentials_exception

    

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def require_customer(
    user: dict = Depends(get_current_user)
):
    if user.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Customers only."
        )
    return user
