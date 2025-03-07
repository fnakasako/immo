from fastapi import FastAPI
from fastapi.middlewares.cors import CORSMiddleware
from app.api.routes import novel
from app.core.config import settings

app = FastAPI(
    title= "Immo API",
    description = "AI-powered creative writing platform",
    version = "0.1.0"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}