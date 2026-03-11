from contextlib import asynccontextmanager

from fastapi import FastAPI

from smm.api.v1 import auth, oauth, posts, social_accounts, users
from smm.scheduler.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = start_scheduler()
    yield
    stop_scheduler(scheduler)


app = FastAPI(
    title="Social Media Manager",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    social_accounts.router, prefix="/api/v1/social-accounts", tags=["social-accounts"]
)
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
