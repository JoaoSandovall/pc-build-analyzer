import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from rate_limiter import limiter
from routers import auth, budgets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app = FastAPI(title="PC Build Analyzer API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL], 
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept"], 
)

app.include_router(auth.router)
app.include_router(budgets.router)

@app.get("/", tags=["Health Check"])
def root():
    return {"status": "online", "message": "API rodando perfeitamente e refatorada."}