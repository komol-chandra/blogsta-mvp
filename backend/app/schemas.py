from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Users ----------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileOut(UserOut):
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    post_count: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_following: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Posts ----------
class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


class RepostCreate(BaseModel):
    content: Optional[str] = ""


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    image_url: Optional[str] = None
    created_at: datetime
    author: UserOut
    reaction_count: int = 0
    my_reaction: Optional[str] = None
    comment_count: int = 0
    repost_count: int = 0
    repost_of: Optional["PostOut"] = None


# ---------- Comments ----------
class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    created_at: datetime
    author: UserOut


# ---------- Reactions ----------
class ReactionCreate(BaseModel):
    type: Literal["like", "love", "haha", "wow", "sad", "angry"] = "like"


class ReactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    user: UserOut
