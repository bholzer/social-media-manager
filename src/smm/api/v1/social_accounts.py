import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smm.dependencies import get_current_user, get_session
from smm.models.user import User
from smm.schemas.social_account import SocialAccountCreate, SocialAccountResponse
from smm.services.social_account import SocialAccountService

router = APIRouter()


@router.post(
    "/", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_social_account(
    data: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SocialAccountService(session)
    account = await service.create(current_user.id, data)
    return account


@router.get("/", response_model=list[SocialAccountResponse])
async def list_social_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SocialAccountService(session)
    return await service.list(current_user.id)


@router.get("/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SocialAccountService(session)
    account = await service.get(current_user.id, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = SocialAccountService(session)
    deleted = await service.delete(current_user.id, account_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
