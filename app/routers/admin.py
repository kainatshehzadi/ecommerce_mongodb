from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, HTTPException, Depends,Query
from app.db.database import get_db
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.schemas.user import CreateUser, UserOut
from app.utils.auth import hash_password
from app.utils.depends import require_admin
from bson import ObjectId
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/create/users", response_model=UserOut)
async def create_customer(
    user: CreateUser,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin)
):

    if db is None:
       raise HTTPException(status_code=500, detail="Database not connected!")

    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["role"] = "customer"

    result = await db.users.insert_one(user_dict)
    print("Inserted user ID:", result.inserted_id)  

    created_user = await db.users.find_one({"_id": result.inserted_id})
    print("Retrieved user:", created_user)  

    return {
        "id": str(created_user["_id"]),
        "email": created_user["email"],
        "username": created_user["username"],
        "phone": created_user["phone"]
    }
@router.get("/Read all/users", response_model=list[UserOut])
async def get_all_customers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin)
):
    customers_cursor = db.users.find({"role": "customer"})
    customers = await customers_cursor.to_list(length=100)

    db_users = []
    for customer in customers:
        customer["id"] = str(customer["_id"])
        customer.pop("_id", None)
        
        
        customer["phone"] = customer.get("phone", "") 

        db_users.append(customer)

    return [UserOut(**user) for user in db_users]

@router.post("/create/products", response_model=ProductOut)
async def create_product(
    product_data: ProductCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(require_admin)  
):
    product_dict = product_data.dict()
    product_dict['image_url'] = str(product_dict['image_url'])
    result = await db.products.insert_one(product_dict)
    created_product = await db.products.find_one({"_id": result.inserted_id})
    created_product["id"] = str(created_product["_id"])
    return created_product

@router.put("/update/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    update: ProductUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    existing = await db.products.find_one({"_id": ObjectId(product_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

 
    update_data = update.dict(exclude_unset=True)
    if 'image_url' in update_data:
        update_data['image_url'] = str(update_data['image_url'])

    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    updated = await db.products.find_one({"_id": ObjectId(product_id)})
    return {**updated, "id": str(updated["_id"])}

ALLOWED_STATUSES = {"pending", "confirmed", "shipped", "delivered"}
@router.delete("/delete/products/{product_id}")
async def soft_delete_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    result = await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"is_deleted": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"detail": "Product soft-deleted successfully"}


@router.get("/product")
async def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin)
):
    filter_query = {"$or": [{"is_deleted": False}, {"is_deleted": {"$exists": False}}]}
    cursor = db.products.find(filter_query).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)

    total_count = await db.products.count_documents(filter_query)
    total_pages = (total_count + limit - 1) // limit

    product_list = []
    for p in products:
        p["id"] = str(p["_id"])
        p.pop("_id", None)
        product_list.append(p)

    return JSONResponse({
        "products": product_list,
        "pagination": {
            "total_items": total_count,
            "total_pages": total_pages,
            "current_page": (skip // limit) + 1,
            "page_size": limit,
            "skip": skip
        }
    })


@router.get("/read-all/orders", response_model=list[OrderOut])
async def get_all_orders(db: AsyncIOMotorDatabase = Depends(get_db), admin=Depends(require_admin)):
    orders = await db.orders.find().to_list(length=None)
    return [
        {
            "id": str(order["_id"]),
            "user_id": str(order["user_id"]),
            "items": order["items"],
            "total_price": order["total_price"],
            "status": order.get("status", "pending"),  
            "created_at": order.get("created_at", datetime.now(timezone.utc))
        }
        for order in orders
    ]

@router.get("/read-by-id/orders/{order_id}", response_model=OrderOut)
async def get_order_detail(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db), admin=Depends(require_admin)):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": str(order["_id"]),
        "user_id": str(order["user_id"]),
        "items": order["items"],
        "total_price": order["total_price"],
        "created_at": order.get("created_at"),
        "status": order.get("status")
    }


@router.get("/dashboard", summary="Get basic stats")
async def get_dashboard_stats(db: AsyncIOMotorDatabase = Depends(get_db), admin=Depends(require_admin)):
    total_customers = await db.users.count_documents({"role": "customer"})
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})

    revenue_cursor = db.orders.find({}, {"total_price": 1})
    total_revenue = 0
    async for order in revenue_cursor:
        total_revenue += order.get("total_price", 0)

    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }


@router.patch("/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(require_admin),
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    new_status = status_update.status.lower()
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed: {', '.join(ALLOWED_STATUSES)}"
        )

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": new_status}}
    )

    return {"message": f"Order status updated to '{new_status}'"}