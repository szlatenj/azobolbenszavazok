from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import VotingGuideSignup
from app.schemas import SignupRequest, SignupResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=SignupResponse, status_code=201)
@limiter.limit(settings.signup_rate_limit)
async def create_signup(
    request: Request,
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(VotingGuideSignup).where(VotingGuideSignup.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    signup = VotingGuideSignup(
        name=data.name,
        email=data.email,
        phone=data.phone,
        voting_method=data.voting_method,
        language_pref=data.language_pref,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(signup)
    await db.commit()

    return SignupResponse(message="Signup successful")
