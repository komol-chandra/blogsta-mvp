from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import post as post_crud
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["posts"])


@router.post("/posts", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(data: schemas.PostCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    post = post_crud.create(db, current_user.id, data)
    return post_crud.get_with_counts(db, post.id, current_user.id)


@router.get("/feed", response_model=list[schemas.PostOut])
def get_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return post_crud.feed(db, skip, limit)


@router.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = post_crud.get_with_counts(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, data: schemas.PostUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    post = post_crud.get(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    post_crud.update(db, post, data)
    return post_crud.get_with_counts(db, post_id, current_user.id)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    post = post_crud.get(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    post_crud.delete(db, post)


@router.post("/posts/{post_id}/repost", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def repost(post_id: int, data: schemas.RepostCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    new_post = post_crud.repost(db, current_user.id, post_id, data)
    if not new_post:
        raise HTTPException(status_code=404, detail="Original post not found")
    return post_crud.get_with_counts(db, new_post.id, current_user.id)
