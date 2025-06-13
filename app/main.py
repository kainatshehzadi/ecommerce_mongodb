from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.db.database import connect_to_mongo
from app.routers import auth, admin,order,customer
from app.utils.error_handler import validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="E-Commerce API")

# Initialize FastAPI app without docs
app = FastAPI(
    title="E-commerce API",
    docs_url=None,    # Disable Swagger UI
    redoc_url=None,   # Disable ReDoc
    openapi_url=None  # Disable OpenAPI schema
)
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.get("/")
async def root():
    return {"message": "Welcome to the eCommerce API"}

# Allow all for testing
origins = [
    "http://localhost:3000", 
    "https://your-frontend-domain.com",  
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(customer.router,tags=["Products (Customer)"])
app.include_router(order.router,tags=["Orders"])
app.add_exception_handler(RequestValidationError, validation_exception_handler)