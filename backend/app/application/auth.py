from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.setup import get_db
from app.persistence.security import verify_session
from app.persistence.user_repository import get_by_id

def get_current_user(
    session: str | None = Cookie(default=None, alias="session"),
    db: Session = Depends(get_db),
):
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user_id = verify_session(session)
    if user_id is None: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token"
        )

    user = get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
        )
    return user
