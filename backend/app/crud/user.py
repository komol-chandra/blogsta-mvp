from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..auth import hash_password


def get_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create(db: Session, data: schemas.UserCreate):
    user = models.User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: models.User, data: schemas.UserUpdate):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def follow(db: Session, follower_id: int, following_id: int):
    if follower_id == following_id:
        return None
    existing = (
        db.query(models.Follow)
        .filter_by(follower_id=follower_id, following_id=following_id)
        .first()
    )
    if existing:
        return existing
    f = models.Follow(follower_id=follower_id, following_id=following_id)
    db.add(f)
    db.commit()
    return f


def unfollow(db: Session, follower_id: int, following_id: int):
    db.query(models.Follow).filter_by(
        follower_id=follower_id, following_id=following_id
    ).delete()
    db.commit()


def is_following(db: Session, follower_id: int, following_id: int) -> bool:
    return (
        db.query(models.Follow)
        .filter_by(follower_id=follower_id, following_id=following_id)
        .first()
        is not None
    )


def profile_counts(db: Session, user_id: int):
    post_count = db.query(func.count(models.Post.id)).filter(
        models.Post.user_id == user_id
    ).scalar()
    follower_count = db.query(func.count(models.Follow.id)).filter(
        models.Follow.following_id == user_id
    ).scalar()
    following_count = db.query(func.count(models.Follow.id)).filter(
        models.Follow.follower_id == user_id
    ).scalar()
    return post_count or 0, follower_count or 0, following_count or 0
