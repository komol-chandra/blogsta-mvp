from sqlalchemy.orm import Session, joinedload

from .. import models, schemas


def create(db: Session, post_id: int, user_id: int, data: schemas.CommentCreate):
    comment = models.Comment(post_id=post_id, user_id=user_id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_for_post(db: Session, post_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Comment)
        .options(joinedload(models.Comment.author))
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get(db: Session, comment_id: int):
    return db.query(models.Comment).filter(models.Comment.id == comment_id).first()


def delete(db: Session, comment: models.Comment):
    db.delete(comment)
    db.commit()
