from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.schemas.order import OrderCreate, OrderOut
from app.utils.depends import require_customer
from app.db.database import get_db
from datetime import datetime, timezone
router = APIRouter()

@router.post("/create/orders", response_model=OrderOut)
async def place_order(order: OrderCreate, customer=Depends(require_customer)):
    db = get_db()
    total = 0
    validated_items = []

    for item in order.items:
        if not ObjectId.is_valid(item.product_id):
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.product_id}")
        product = await db.products.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        if product["in_stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product['name']}")
        
        total += product["price"] * item.quantity
        validated_items.append(item)

    # Prepare order data with user_id as ObjectId and created_at timestamp
    order_data = {
        "user_id": ObjectId(customer["id"]),
        "items": [item.dict() for item in validated_items],
        "total_price": total,
        "status": order_data.status.value,
        "created_at": datetime.now(timezone.utc)
    }

    result = await db.orders.insert_one(order_data)
    
    # Update stock for each product
    for item in validated_items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"in_stock": -item.quantity}}
        )

    order_record = await db.orders.find_one({"_id": result.inserted_id})

    return {
        "id": str(order_record["_id"]),
        "user_id": str(order_record["user_id"]),
        "items": order_record["items"],
        "total_price": order_record["total_price"],
        "created_at": order_record["created_at"]
    }

@router.get("/all/orders", response_model=list[OrderOut])
async def get_own_orders(customer=Depends(require_customer)):
    db = get_db()
    orders = await db.orders.find({"user_id": ObjectId(customer["id"])}).to_list(length=None)
    return [
        {
            "id": str(order["_id"]),
            "user_id": str(order["user_id"]),
            "items": order["items"],
            "total_price": order["total_price"],
            "created_at": order.get("created_at")
        } for order in orders
    ]


@router.get("/read by id/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, customer=Depends(require_customer)):
    db = get_db()
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order or order["user_id"] != ObjectId(customer["id"]):
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": str(order["_id"]),
        "user_id": str(order["user_id"]),
        "items": order["items"],
        "total_price": order["total_price"],
        "created_at": order.get("created_at")
    }
