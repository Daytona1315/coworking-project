from fastapi import FastAPI

from backend.src.business.router import router as business_router
from backend.src.auth.router import router as auth_router


app = FastAPI()

app.include_router(business_router)
app.include_router(auth_router)
