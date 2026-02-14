from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import VotingGuideHelpRequest
from app.schemas import HelpRequestRequest, HelpRequestResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/help-request", response_model=HelpRequestResponse, status_code=201)
@limiter.limit(settings.helprequest_rate_limit)
async def create_help_request(
    request: Request,
    data: HelpRequestRequest,
    db: AsyncSession = Depends(get_db),
):
    help_request = VotingGuideHelpRequest(
        name=data.name,
        email=data.email,
        phone=data.phone,
        message=data.message,
        voting_method=data.voting_method,
        language_pref=data.language_pref,
        ip_address=request.client.host if request.client else None,
    )
    db.add(help_request)
    await db.commit()

    return HelpRequestResponse(message="Help request submitted successfully")
