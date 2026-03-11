import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smm.dependencies import get_current_user, get_session
from smm.models.post_target import PostTarget, PostTargetStatus
from smm.models.user import User
from smm.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate
from smm.services.post import PostService

router = APIRouter()


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    try:
        post = await service.create(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return post


@router.get("/", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: PostTargetStatus | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    posts, total = await service.list(
        current_user.id, page=page, size=size, status=status_filter
    )
    return PostListResponse(items=posts, total=total, page=page, size=size)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    post = await service.get(current_user.id, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    try:
        post = await service.update(current_user.id, post_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    deleted = await service.delete(current_user.id, post_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )


@router.post("/{post_id}/publish-now", response_model=PostResponse)
async def publish_now(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    post = await service.get(current_user.id, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # Transition eligible targets to publishing
    has_targets = False
    for target in post.targets:
        if target.status in (PostTargetStatus.DRAFT, PostTargetStatus.SCHEDULED):
            target.status = PostTargetStatus.PUBLISHING
            has_targets = True

    if not has_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No targets available to publish",
        )

    await session.commit()

    # Enqueue Dramatiq tasks
    from smm.workers.tasks import publish_target_task

    result = await session.execute(
        select(PostTarget).where(
            PostTarget.post_id == post_id,
            PostTarget.status == PostTargetStatus.PUBLISHING,
        )
    )
    for target in result.scalars().all():
        publish_target_task.send(str(target.id))

    return await service.get(current_user.id, post_id)
