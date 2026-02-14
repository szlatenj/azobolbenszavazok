from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import VotingGuideContact
from app.schemas import ContactRequest, ContactResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/contact", response_model=ContactResponse, status_code=201)
@limiter.limit(settings.contact_rate_limit)
async def create_contact(
    request: Request,
    data: ContactRequest,
    db: AsyncSession = Depends(get_db),
):
    contact = VotingGuideContact(
        name=data.name,
        email=data.email,
        message=data.message,
        language_pref=data.language_pref,
        ip_address=request.client.host if request.client else None,
    )
    db.add(contact)
    await db.commit()

    return ContactResponse(message="Message sent successfully")
