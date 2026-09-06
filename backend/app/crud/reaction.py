from sqlalchemy.orm import Session, joinedload

from .. import models, schemas


def upsert(db: Session, post_id: int, user_id: int, data: schemas.ReactionCreate):
    existing = (
        db.query(models.Reaction).filter_by(post_id=post_id, user_id=user_id).first()
    )
    if existing:
        existing.type = data.type
        db.commit()
        db.refresh(existing)
        return existing
    reaction = models.Reaction(post_id=post_id, user_id=user_id, type=data.type)
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def remove(db: Session, post_id: int, user_id: int):
    db.query(models.Reaction).filter_by(post_id=post_id, user_id=user_id).delete()
    db.commit()


def list_for_post(db: Session, post_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Reaction)
        .options(joinedload(models.Reaction.user))
        .filter(models.Reaction.post_id == post_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
