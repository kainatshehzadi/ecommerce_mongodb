from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str]
    price: float = Field(..., gt=0)
    in_stock: int = Field(..., ge=0)
    image_url: Optional[HttpUrl] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    in_stock: Optional[int]
    image_url: Optional[HttpUrl] = None

class ProductOut(ProductBase):
    id: str
