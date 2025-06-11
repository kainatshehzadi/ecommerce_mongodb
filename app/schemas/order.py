from datetime import datetime
import enum
from pydantic import BaseModel
from typing import List, Optional

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    status: Optional[OrderStatus] = OrderStatus.PENDING

class OrderCreate(BaseModel):
    items: List[OrderItem]

class OrderOut(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    total_price: float
    status: OrderStatus
    created_at: datetime

    class config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus