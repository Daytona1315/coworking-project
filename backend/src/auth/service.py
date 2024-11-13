import jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from pydantic import ValidationError
from sqlalchemy import select, insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette import status
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.database import models
from backend.src.database.async_engine import get_async_session
from backend.src.auth.schema import User, Token, UserCreate
from backend.src.settings import settings


class AuthService:
    """The service for registration and authentication of users."""

    oauth2_schema = OAuth2PasswordBearer(tokenUrl='auth/sign-in')

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_schema)) -> User:
        return AuthService.validate_token(token)

    # OAUTH2 METHODS ----------
    @classmethod
    def verify_password(cls, raw_password: str, hash_password: str) -> bool:
        return bcrypt.verify(raw_password, hash_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    @classmethod
    def validate_token(cls, token: str) -> User:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail='Cannot validate token'
            )

        user_data = payload.get('user')

        try:
            user = User.model_validate(user_data)
        except ValidationError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail='Cannot validate token'
            )

        return user

    @classmethod
    def create_token(cls, user: User) -> Token:
        user_data = user.model_dump()
        now = datetime.now()
        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.jwt_expiration),
            'sub': str(user_data['id']),
            'user': user_data,
        }
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        return Token(access_token=token)

    # CREATION OF DATABASE SESSIONS ----------
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    # USER REGISTRATION METHOD ----------
    async def register_new_user(self, user_data: UserCreate) -> Token:
        try:
            # Добавляем нового пользователя в базу данных и получаем id
            async with self.session.begin():
                user_stmt = insert(models.User).values(
                    username=user_data.username,
                    email=user_data.email
                ).returning(models.User.id)
                user_result = await self.session.execute(user_stmt)
                user_id = user_result.scalar()

                # Добавляем учетные данные пользователя в таблицу CredentialsLocal
                credentials_stmt = insert(models.Credential).values(
                    user_id=user_id,
                    email=user_data.email,
                    hashed_password=self.hash_password(user_data.password)
                )
                await self.session.execute(credentials_stmt)

                # Создаем токен
                user = User(id=user_id, email=user_data.email, username=user_data.username)
                token = self.create_token(user)

        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User already exists")

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

        return token

    # USER AUTHENTICATION METHOD ----------
    async def authenticate_user(self, email: str, password: str) -> Token:
        try:
            async with self.session.begin():
                user_stmt = select(models.User, models.Credential).join(
                    models.Credential, models.Credential.user_id == models.User.id
                ).filter(models.Credential.email == email)
                user_result = await self.session.execute(user_stmt)
                user, credentials = user_result.scalar()

                if not user:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

                if not self.verify_password(password, credentials.hashed_password):
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

                token = self.create_token(user)
                return token

        except SQLAlchemyError:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
