from fastapi import APIRouter, HTTPException, Depends,status
from app.schemas.user import UserCreate, Token, UserLogin, UserResponse
from app.utils.auth import hash_password, verify_password, create_access_token
from app.db.database import get_db
from bson import ObjectId


router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    # Check the role passed
    if user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=" Only admin can sign up."
        )

    db = get_db()
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["role"] = "admin"

    await db.users.insert_one(user_dict)

    return {"message": " Admin registered successfully. Please log in."}


@router.post("/login", response_model=Token)
async def login(user: UserLogin):  
    db = get_db()
    print("Login requested for:", user.email)

    existing = await db.users.find_one({"email": user.email})
    if not existing:
        print(" No user found with email:", user.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    print(" Found user:", existing)
    if not verify_password(user.password, existing["password"]):
        print(" Password mismatch")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    print(" Password verified, creating token...")

    token = create_access_token({
        "sub": existing["email"],
        "role": existing["role"],
        "id": str(existing["_id"])
    })
    return {"access_token": token}
