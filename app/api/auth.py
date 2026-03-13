"""Authentication router for user registration and login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user
from app.domain.models import User
from app.domain.schemas import ErrorResponse, TokenResponse, UserCreate, UserLogin, UserResponse
from app.infrastructure.database import get_db
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new API user",
    responses={
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    user = auth_service.register_user(db, payload)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and get JWT access token",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate_user(db, username=payload.username, password=payload.password)
    token, expires_in = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
    },
)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
