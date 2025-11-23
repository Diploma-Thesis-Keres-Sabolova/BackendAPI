from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

@router.get("/")
def health(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
