import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s — %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SpendSense API", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security middleware ────────────────────────────────────────────────────────
from middleware.security import SecurityHeadersMiddleware, limiter  # noqa: E402

app.add_middleware(SecurityHeadersMiddleware)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait before trying again."},
    )

# ── Routers ────────────────────────────────────────────────────────────────────
from routers import auth, transactions, purchases, nudges, reports  # noqa: E402

app.include_router(auth.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(purchases.router, prefix="/api/v1")
app.include_router(nudges.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    from db.mongodb import init_db  # noqa: PLC0415
    from db.bigquery import init_bigquery  # noqa: PLC0415

    init_db()
    init_bigquery()


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "SpendSense API", "version": "1.0.0"}
