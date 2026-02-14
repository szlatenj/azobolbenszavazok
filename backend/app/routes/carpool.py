from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import VotingGuideCarpool
from app.schemas import CarpoolRequest, CarpoolResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/carpool", response_model=CarpoolResponse, status_code=201)
@limiter.limit(settings.carpool_rate_limit)
async def create_carpool(
    request: Request,
    data: CarpoolRequest,
    db: AsyncSession = Depends(get_db),
):
    if data.carpool_type == "offer" and data.seats is None:
        raise HTTPException(status_code=422, detail="Seats required for carpool offers")

    carpool = VotingGuideCarpool(
        carpool_type=data.carpool_type,
        name=data.name,
        email=data.email,
        phone=data.phone,
        starting_location=data.starting_location,
        seats=data.seats,
        voting_method=data.voting_method,
        language_pref=data.language_pref,
        ip_address=request.client.host if request.client else None,
    )
    db.add(carpool)
    await db.commit()

    return CarpoolResponse(message="Carpool submission successful")
