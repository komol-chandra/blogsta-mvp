from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models  # noqa: F401  (registers models on Base.metadata)
from .routers import auth, users, posts, comments, reactions

# For MVP: auto-create tables. Swap for Alembic migrations once schema stabilizes.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blogsta API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(reactions.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "blogsta-api"}
