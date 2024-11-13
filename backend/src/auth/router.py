from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.src.auth.schema import (
    UserCreate, Token, BaseUser
)
from backend.src.auth.service import AuthService


router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)


# Регистрация пользователя
@router.post('/sign-up', response_model=Token)
async def sign_up(user_data: UserCreate,
                  service: AuthService = Depends()
                  ):
    try:
        token = await service.register_new_user(user_data)
        return token
    except ConnectionRefusedError:
        raise HTTPException(
            503,
            detail="Service Unavailable"
        )


# Вход пользователя
@router.post('/sign-in', response_model=Token)
async def sign_in(form_data: OAuth2PasswordRequestForm = Depends(),
                  service: AuthService = Depends()
                  ):
    try:
        token = await service.authenticate_user(
            form_data.username,  # Здесь нужно передавать e-mail
            form_data.password,
        )
        return token
    except ConnectionRefusedError:
        raise HTTPException(
            503,
            detail="Service Unavailable"
        )


# Получить данные пользователя
@router.get('/user', response_model=BaseUser)
def get_user(user: BaseUser = Depends(AuthService.get_current_user)):
    try:
        return user
    except ConnectionRefusedError:
        raise HTTPException(
            503,
            detail="Service Unavailable"
        )
