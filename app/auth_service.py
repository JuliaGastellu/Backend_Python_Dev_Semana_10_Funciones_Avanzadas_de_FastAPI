from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import DuplicateError, UnauthorizedError
from app.models import RefreshToken, User
from app.schemas import RegisterRequest, TokenPair
from app.security import create_token, decode_token, hash_jti, hash_password, verify_password


class AuthService:
    def __init__(self, db: AsyncSession) -> None: self.db = db

    async def register(self, data: RegisterRequest) -> User:
        exists = await self.db.scalar(select(User.id).where(or_(User.username == data.username, User.email == data.email)))
        if exists: raise DuplicateError("El username o email ya está registrado")
        user = User(username=data.username, email=data.email, role="user", hashed_password=hash_password(data.password))
        self.db.add(user); await self.db.commit(); await self.db.refresh(user); return user

    async def authenticate(self, username: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.username == username))
        if not user or not user.is_active or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Las credenciales no son válidas")
        return user

    async def issue_pair(self, user: User) -> TokenPair:
        access, _, _ = create_token(user.id, user.role, "access", timedelta(minutes=settings.access_token_minutes))
        refresh, jti, expires = create_token(user.id, user.role, "refresh", timedelta(days=settings.refresh_token_days))
        self.db.add(RefreshToken(jti_hash=hash_jti(jti), user_id=user.id, expires_at=expires))
        await self.db.commit(); return TokenPair(access_token=access, refresh_token=refresh)

    async def rotate(self, raw_token: str) -> TokenPair:
        payload = decode_token(raw_token, "refresh"); token_hash = hash_jti(payload["jti"])
        stored = await self.db.scalar(select(RefreshToken).where(RefreshToken.jti_hash == token_hash).with_for_update())
        if not stored or stored.revoked_at:
            if stored: await self.db.execute(update(RefreshToken).where(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc))); await self.db.commit()
            raise UnauthorizedError("El refresh token fue revocado o reutilizado")
        if stored.expires_at <= datetime.now(timezone.utc): raise UnauthorizedError("El refresh token venció")
        user = await self.db.get(User, stored.user_id)
        if not user or not user.is_active: raise UnauthorizedError("El usuario no está disponible")
        stored.revoked_at = datetime.now(timezone.utc)
        pair = await self.issue_pair(user)
        replacement = decode_token(pair.refresh_token, "refresh")
        stored.replaced_by_hash = hash_jti(replacement["jti"])
        await self.db.commit(); return pair

    async def logout(self, raw_token: str) -> None:
        payload = decode_token(raw_token, "refresh")
        stored = await self.db.scalar(select(RefreshToken).where(RefreshToken.jti_hash == hash_jti(payload["jti"])))
        if stored and stored.revoked_at is None: stored.revoked_at = datetime.now(timezone.utc); await self.db.commit()
