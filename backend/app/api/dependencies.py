from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.generation import GenerationCoordinator

def get_db() -> Generator:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_generation_service() -> GenerationCoordinator:
    """Generation service dependency"""
    return GenerationCoordinator()
