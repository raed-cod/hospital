from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, session
from app.models.appointments.router import router as appointment_router
from app.models.billing.router import router as invoice_router
from app.models.medical_records.router import router as medical_router
from app.models.scheduling.router import router as scheduling_router
from app.models.users import init_first_admin
from app.models.users.router import router as users_router
from app.payment.router import router as payment_router


# Lifecycle context manager to initialize database schemas and default admin user
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = session()
    try:
        init_first_admin(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="Hospital Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application Routers
app.include_router(users_router)
app.include_router(scheduling_router)
app.include_router(appointment_router)
app.include_router(medical_router)
app.include_router(invoice_router)
app.include_router(payment_router)


@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Hospital Management System API!"}