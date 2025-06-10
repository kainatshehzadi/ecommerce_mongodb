from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.db.database import get_db
from app.schemas.product import ProductOut

router = APIRouter()

@router.get("/", response_model=list[ProductOut])
async def list_products():
    db = get_db()
    products = await db.products.find().to_list(length=None)
    return [{**p, "id": str(p["_id"])} for p in products]

@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str):
    db = get_db()
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {**product, "id": str(product["_id"])}
