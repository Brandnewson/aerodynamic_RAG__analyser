"""Authentication service for user registration and login."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.core.security import hash_password, verify_password
from app.domain.models import User
from app.domain.schemas import UserCreate


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def register_user(db: Session, payload: UserCreate) -> User:
    existing = get_user_by_username(db, payload.username)
    if existing is not None:
        raise UserAlreadyExistsError(payload.username)

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user
