from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .. import models, schemas


def _attach_counts(db: Session, post: models.Post, current_user_id: int | None):
    reaction_count = db.query(func.count(models.Reaction.id)).filter(
        models.Reaction.post_id == post.id
    ).scalar() or 0
    comment_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.post_id == post.id
    ).scalar() or 0
    repost_count = db.query(func.count(models.Post.id)).filter(
        models.Post.repost_of_id == post.id
    ).scalar() or 0

    my_reaction = None
    if current_user_id:
        r = (
            db.query(models.Reaction)
            .filter_by(post_id=post.id, user_id=current_user_id)
            .first()
        )
        my_reaction = r.type if r else None

    post.reaction_count = reaction_count
    post.comment_count = comment_count
    post.repost_count = repost_count
    post.my_reaction = my_reaction
    return post


def create(db: Session, user_id: int, data: schemas.PostCreate):
    post = models.Post(user_id=user_id, content=data.content, image_url=data.image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def repost(db: Session, user_id: int, original_post_id: int, data: schemas.RepostCreate):
    original = get(db, original_post_id)
    if not original:
        return None
    new_post = models.Post(
        user_id=user_id,
        content=data.content or "",
        repost_of_id=original.id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def get(db: Session, post_id: int):
    return (
        db.query(models.Post)
        .options(joinedload(models.Post.author), joinedload(models.Post.repost_of))
        .filter(models.Post.id == post_id)
        .first()
    )


def get_with_counts(db: Session, post_id: int, current_user_id: int | None = None):
    post = get(db, post_id)
    if not post:
        return None
    return _attach_counts(db, post, current_user_id)


def feed(db: Session, skip: int = 0, limit: int = 20, current_user_id: int | None = None):
    posts = (
        db.query(models.Post)
        .options(joinedload(models.Post.author), joinedload(models.Post.repost_of))
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_attach_counts(db, p, current_user_id) for p in posts]


def by_user(db: Session, user_id: int, skip: int = 0, limit: int = 20, current_user_id: int | None = None):
    posts = (
        db.query(models.Post)
        .options(joinedload(models.Post.author), joinedload(models.Post.repost_of))
        .filter(models.Post.user_id == user_id)
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_attach_counts(db, p, current_user_id) for p in posts]


def update(db: Session, post: models.Post, data: schemas.PostUpdate):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


def delete(db: Session, post: models.Post):
    db.delete(post)
    db.commit()
