from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, HTTPException, Depends
from app import db
from app.db.database import get_db
from app.schemas.order import OrderOut
from app.schemas.user import CreateUser, UserOut
from app.utils.auth import hash_password
from app.utils.depends import require_admin
from bson import ObjectId
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter()

@router.post("/create-customer", response_model=UserOut)
async def create_customer(user: CreateUser, admin=Depends(require_admin)):
    db = get_db()

    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["role"] = "customer" 

    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    return {
        "id": str(created_user["_id"]),
        "email": created_user["email"],
        "username": created_user["username"],
        "phone_num": created_user["phone_num"]
    }
@router.get("/customers", response_model=list[UserOut])
async def get_all_customers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin) 
):
    customers_cursor = db.customers.find()
    customers = await customers_cursor.to_list(length=100)

    for customer in customers:
        customer["id"] = str(customer["_id"])
        customer.pop("_id", None)

    return customers


@router.post("/", response_model=ProductOut)
async def create_product(
    product_data: ProductCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(require_admin)  
):
    product_dict = product_data.dict()
    result = await db.products.insert_one(product_dict)
    created_product = await db.products.find_one({"_id": result.inserted_id})
    created_product["id"] = str(created_product["_id"])
    return created_product

@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, update: ProductUpdate, admin=Depends(require_admin)):
    db = get_db()
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    existing = await db.products.find_one({"_id": ObjectId(product_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {k: v for k, v in update.dict().items() if v is not None}}
    )
    updated = await db.products.find_one({"_id": ObjectId(product_id)})
    return {**updated, "id": str(updated["_id"])}


@router.delete("/{product_id}")
async def delete_product(product_id: str, admin=Depends(require_admin)):
    db = get_db()
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    result = await db.products.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"detail": "Product deleted successfully"}


@router.get("/product", response_model=list[ProductOut])
async def get_all_products(admin=Depends(require_admin)):
    db = get_db()
    cursor = db.products.find()
    products = await cursor.to_list(length=None)
    return [{**p, "id": str(p["_id"])} for p in products]
@router.get("/orders", response_model=list[OrderOut])
async def get_all_orders(admin=Depends(require_admin)):
    db = get_db()
    orders = await db.orders.find().to_list(length=None)
    return [
        {
            "id": str(order["_id"]),
            "user_id": order["user_id"],
            "items": order["items"],
            "total_price": order["total_price"]
        } for order in orders
    ]

@router.get("/{order_id}", response_model=OrderOut)
async def get_order_detail(order_id: str, admin=Depends(require_admin)):
    db = get_db()
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": str(order["_id"]),
        "user_id": order["user_id"],
        "items": order["items"],
        "total_price": order["total_price"]
    }
@router.get("/dashboard", summary="Get basic stats")
async def get_dashboard_stats(admin=Depends(require_admin)):
    db = get_db()
    total_customers = await db.users.count_documents({"role": "customer"})
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})
    revenue_cursor = db.orders.find({}, {"total_price": 1})
    revenue = sum([(order["total_price"]) async for order in revenue_cursor])
    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": revenue
    }
