from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.contacts import router as contacts_router
from app.routers.payments import router as payments_router
from app.routers.buyers import router as buyers_router
from app.routers.transactions import router as transactions_router

from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.sales import router as sales_router
from app.routers.pricing import router as pricing_router
from app.routers.health import router as health_router
from app.routers.suppliers import router as suppliers_router
from app.routers.warehouses import router as warehouses_router
from app.routers.purchases import router as purchases_router
from app.routers.inventory import router as inventory_router
from app.routers.purchase_payments import router as purchase_payments_router

app = FastAPI(title="Shop System", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(customers_router)
app.include_router(contacts_router)
app.include_router(products_router)
app.include_router(sales_router)
app.include_router(payments_router)
app.include_router(buyers_router)
app.include_router(pricing_router)
app.include_router(suppliers_router)
app.include_router(warehouses_router)
app.include_router(purchases_router)
app.include_router(inventory_router)
app.include_router(purchase_payments_router)

app.include_router(transactions_router)
