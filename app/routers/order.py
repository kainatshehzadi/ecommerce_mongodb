from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from bson import ObjectId
from app.schemas.order import OrderCreate, OrderOut
from app.utils.depends import require_customer
from app.db.database import get_db
from datetime import datetime, timezone
from app.utils.email import send_order_email_to_admin
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/create/orders", response_model=OrderOut)
async def place_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
    customer=Depends(require_customer)
):
    total = 0
    validated_items = []

    for item in order.items:
        if not ObjectId.is_valid(item.product_id):
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.product_id}")
        
        product = await db.products.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        
        stock = product.get("stock")

        if stock is None:
            raise HTTPException(status_code=500, detail=f"'in_stock' field is missing in product {item.product_id}")

        try:
            stock = int(stock)
        except (ValueError, TypeError):
            raise HTTPException(status_code=500, detail=f"'in_stock' is not a valid number in product {item.product_id}")

        if stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.get('name', 'Unknown Product')}")

        total += product["price"] * item.quantity
        validated_items.append(item)

    order_data = {
        "user_id": (customer["_id"]),
        "items": [item.dict() for item in validated_items],
        "total_price": total,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }

    result = await db.orders.insert_one(order_data)

    for item in validated_items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"in_stock": -item.quantity}}
        )

    background_tasks.add_task(
        send_order_email_to_admin,
        customer_name=customer["username"],
        customer_email=customer["email"],
        items=[item.dict() for item in validated_items],
        total_price=total,
        order_id=str(result.inserted_id)
)

    order_record = await db.orders.find_one({"_id": result.inserted_id})

    return {
        "id": str(order_record["_id"]),
        "user_id": str(order_record["user_id"]),
        "items": order_record["items"],
        "total_price": order_record["total_price"],
        "created_at": order_record["created_at"],
        "status": order_record["status"]
    }



@router.get("/read by id/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, customer=Depends(require_customer)):
    db = get_db()
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order or order["user_id"] != customer["_id"]:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": str(order["_id"]),
        "user_id": str(order["user_id"]),
        "items": order["items"],
        "total_price": order["total_price"],
        "created_at": order.get("created_at"),
        "status": order.get("status")
    }
@router.get("/all/orders", response_model=List[OrderOut])
async def get_my_orders(customer=Depends(require_customer)):
    db = get_db()
    
    # Print debug info
    #print("customer:", customer)

    # Access the correct key
    customer_id = ObjectId(customer["_id"])  

    cursor = db.orders.find({"user_id": customer_id})
    orders = await cursor.to_list(length=None)

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    return [
        {
            "id": str(order["_id"]),
            "user_id": str(order["user_id"]),
            "items": order["items"],
            "total_price": order["total_price"],
            "created_at": order.get("created_at"),
            "status": order.get("status"),
        }
        for order in orders
    ]


    return result