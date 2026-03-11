import datetime
import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smm.dependencies import get_current_user, get_session
from smm.models.social_account import Platform, SocialAccount
from smm.models.user import User
from smm.services.facebook_oauth import (
    build_authorize_url,
    exchange_code,
    generate_state,
    get_long_lived_token,
    get_user_pages,
    get_user_profile,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory state store. For production, use Redis or DB.
# Maps state -> {user_id, created_at}
_oauth_states: dict[str, dict] = {}


class FacebookPageResponse(BaseModel):
    page_id: str
    name: str


class FacebookPagesResponse(BaseModel):
    pages: list[FacebookPageResponse]
    oauth_user_token: str


class ConnectPageRequest(BaseModel):
    page_id: str
    page_name: str
    oauth_user_token: str


@router.get("/facebook/connect")
async def facebook_connect(
    current_user: User = Depends(get_current_user),
):
    """Redirect user to Facebook to authorize the app."""
    state = generate_state()
    _oauth_states[state] = {
        "user_id": str(current_user.id),
        "created_at": datetime.datetime.now(datetime.UTC),
    }
    url = build_authorize_url(state)
    return RedirectResponse(url=url)


@router.get("/facebook/callback")
async def facebook_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Handle Facebook OAuth callback.

    Returns the user's Facebook Pages so they can choose which to connect.
    """
    # Validate state
    state_data = _oauth_states.pop(state, None)
    if state_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )

    # Check state age (10 min max)
    age = datetime.datetime.now(datetime.UTC) - state_data["created_at"]
    if age.total_seconds() > 600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state expired",
        )

    user_id = uuid.UUID(state_data["user_id"])

    # Exchange code for tokens
    try:
        short_tokens = await exchange_code(code)
        long_tokens = await get_long_lived_token(
            short_tokens.access_token
        )
    except httpx.HTTPError:
        logger.exception("Facebook token exchange failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Facebook authentication failed",
        )

    # Get pages the user manages
    try:
        pages = await get_user_pages(long_tokens.access_token)
    except httpx.HTTPError:
        logger.exception("Failed to fetch Facebook pages")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Facebook authentication failed",
        )

    if not pages:
        # No pages — connect the user's personal profile instead
        try:
            profile = await get_user_profile(long_tokens.access_token)
        except httpx.HTTPError:
            logger.exception("Failed to fetch Facebook profile")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Facebook authentication failed",
            )

        account = SocialAccount(
            user_id=user_id,
            platform=Platform.FACEBOOK,
            platform_user_id=profile["id"],
            access_token=long_tokens.access_token,
            token_expires_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=long_tokens.expires_in),
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return {
            "message": "Facebook profile connected",
            "account_id": str(account.id),
            "platform_user_id": profile["id"],
            "name": profile.get("name"),
        }

    # Return pages for the user to choose
    return FacebookPagesResponse(
        pages=[
            FacebookPageResponse(page_id=p.page_id, name=p.name)
            for p in pages
        ],
        oauth_user_token=long_tokens.access_token,
    )


@router.post("/facebook/connect-page")
async def connect_facebook_page(
    data: ConnectPageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Connect a specific Facebook Page after OAuth callback."""
    # Get the page's own long-lived access token
    try:
        pages = await get_user_pages(data.oauth_user_token)
    except httpx.HTTPError:
        logger.exception("Failed to fetch pages")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Facebook authentication failed",
        )

    page = next((p for p in pages if p.page_id == data.page_id), None)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found or not managed by this user",
        )

    # Check if already connected
    existing = await session.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == Platform.FACEBOOK,
            SocialAccount.platform_user_id == page.page_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Facebook page is already connected",
        )

    # Page tokens obtained via a long-lived user token don't expire
    account = SocialAccount(
        user_id=current_user.id,
        platform=Platform.FACEBOOK,
        platform_user_id=page.page_id,
        access_token=page.access_token,
        token_expires_at=None,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    return {
        "message": f"Facebook page '{page.name}' connected",
        "account_id": str(account.id),
        "platform_user_id": page.page_id,
        "name": page.name,
    }
