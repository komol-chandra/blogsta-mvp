from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import reaction as reaction_crud, post as post_crud
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["reactions"])


@router.post("/posts/{post_id}/reactions", response_model=schemas.ReactionOut, status_code=status.HTTP_201_CREATED)
def react(post_id: int, data: schemas.ReactionCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    post = post_crud.get(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return reaction_crud.upsert(db, post_id, current_user.id, data)


@router.delete("/posts/{post_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
def unreact(post_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reaction_crud.remove(db, post_id, current_user.id)


@router.get("/posts/{post_id}/reactions", response_model=list[schemas.ReactionOut])
def list_reactions(post_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return reaction_crud.list_for_post(db, post_id, skip, limit)
